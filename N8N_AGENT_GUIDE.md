# راه‌اندازی ایجنت در n8n

این راهنما فرض می‌کنه FastAPI‌ت (`uvicorn app.main:app`) از قبل روی یه
آدرس در دسترسِ n8n اجرا می‌شه. اگه n8n رو لوکال روی همون سیستم داری،
آدرس می‌شه `http://localhost:8000`. اگه n8n cloud یا سرور جداست، باید
FastAPI رو deploy کنی یا با یه tunnel (مثل ngrok) موقتاً در دسترس بذاری.

## ۱. Webhook Trigger

- یه Workflow جدید بساز، اولین نود: **Webhook**
- Method: `POST`
- Path: هرچی خواستی (مثلاً `lipstick-agent`)
- Response Mode: **Using 'Respond to Webhook' node** (چون آخر کار می‌خوایم خودمون فرمت جواب رو کنترل کنیم)
- **مهم برای CORS**: چون این webhook قراره از یه ویجت وب (روی دامنه‌های مختلف) صدا زده بشه، توی تنظیمات نود Webhook گزینه‌ی `Allow CORS` / `Response Headers` رو باز کن و این هدر رو اضافه کن:
  ```
  Access-Control-Allow-Origin: *
  ```
  (برای production بهتره به‌جای `*`، دامنه‌های واقعی مشتری‌هات رو لیست کنی)

ورودی که از ویجت میاد (طراحیش رو پایین‌تر می‌بینی) یه `multipart/form-data` هست شامل:
- `message` (متن پیام کاربر)
- `session_id` (شناسه‌ی مکالمه، برای حافظه)
- `image` (فایل عکس، اختیاری)

## ۲. AI Agent

نود بعدی: **AI Agent** (از دسته‌ی LangChain nodes)

- **Chat Model**: یه OpenAI Chat Model وصل کن. چون AvalAI هم OpenAI-compatible هست، می‌تونی از همون credential استفاده کنی: Base URL رو بذار `https://api.avalai.ir/v1` و API Key رو از AvalAI بذار. مدل رو یه چیز متنی معمولی انتخاب کن (نه qwen-image-edit — اون فقط برای ویرایش عکسه؛ اینجا یه مدل چت متنی لازمه، هرچی AvalAI براش chat completions می‌ده).
- **Memory**: یه `Simple Memory` یا `Window Buffer Memory` وصل کن، با کلید `session_id` (که از ورودی webhook میاد) تا مکالمه‌ی هر کاربر جدا نگه داشته بشه.
- **System Prompt** (این رو دقیقاً بذار، یا بر اساس سلیقه تنظیمش کن):

```
تو دستیار مجازی یه فروشگاه رژ لب هستی. سه تا قابلیت داری که باید از
طریق ابزارهای زیر انجامشون بدی:

۱) list_products — لیست کامل محصولات کاتالوگ (id، نام، رنگ) رو
   برمی‌گردونه. هر وقت لازم شد بدونی چه محصولاتی هست یا اسم محصولی که
   کاربر گفته رو به id تبدیل کنی، این رو صدا بزن.

۲) apply_lipstick — وقتی کاربر می‌خواد ببینه یه رژ خاص روی عکسش چه
   شکلیه، این رو با product_id درست صدا بزن. اگه کاربر عکس نفرستاده،
   ازش بخواه اول عکس چهره‌ی frontal با نور یکنواخت بفرسته. اگه اسم
   محصول رو نمی‌دونی کدوم id هست، اول list_products رو صدا بزن.

۳) recommend_lipstick — وقتی کاربر می‌پرسه «چه رژی بهم میاد؟» یا
   می‌خواد پیشنهاد رژ بگیره، این رو صدا بزن (نیاز به عکس چهره داره).
   نتیجه شامل رتبه‌بندی واقعی محصولات کاتالوگ بر اساس تن پوستشه —
   هرگز خودت رنگ یا محصول جدید پیشنهاد نده که توی کاتالوگ نیست.

۴) live_tryon_info — اگه کاربر پرسید چطور می‌تونه لایو/با وبکم امتحان
   کنه، این رو صدا بزن تا لینک صفحه‌ی لایو رو بهش بدی.

قوانین مهم:
- هرگز رنگ یا محصولی که توی کاتالوگ (list_products) نیست رو پیشنهاد
  نده یا اختراع نکن.
- اگه ابزاری یه image_url برگردوند، توی جواب نهایی‌ت دقیقاً همون لینک
  رو عیناً (بدون تغییر یک حرف) بنویس تا فرانت بتونه نمایشش بده.
- اگه هیچ چهره‌ای توی عکس پیدا نشد (خطای ۴۲۲ از ابزار)، مؤدبانه از
  کاربر بخواه یه عکس واضح‌تر و frontal بفرسته.
- به فارسی و دوستانه جواب بده، مگر کاربر به زبون دیگه‌ای پیام داد.
```

## ۳. تعریف ابزارها (Tools)

روی نود AI Agent، این ۴ ابزار رو اضافه کن (هرکدوم یه sub-node جدا،
معمولاً از نوع **HTTP Request Tool**):

### الف) `list_products`
- Method: `GET`
- URL: `http://localhost:8000/products`
- Description (برای LLM): "لیست همه‌ی محصولات کاتالوگ با id، نام، و رنگ hex رو برمی‌گردونه."
- بدون پارامتر ورودی از طرف LLM.

### ب) `apply_lipstick`
- Method: `POST`
- URL: `http://localhost:8000/apply-lipstick?product_id={product_id}`
- پارامتری که LLM باید پر کنه: `product_id` (عدد، از روی نتیجه‌ی list_products)
- Body Content Type: `Form-Data` / `Multipart`
- یه فیلد باینری اضافه کن با نام `file`، مقدارش رو *به خودِ LLM نسپار* — باید مستقیم به عکسی که کاربر توی همون پیام فرستاده اشاره کنه:
  ```
  {{ $('Webhook').item.binary.image }}
  ```
  (این عبارت داره به نود Webhook اولیه ارجاع می‌ده، نه به چیزی که LLM تولید کرده — چون LLM نمی‌تونه باینری عکس بسازه، فقط می‌تونه بگه *کِی* این ابزار صدا زده بشه و با کدوم product_id)
- Description (برای LLM): "رژ انتخاب‌شده (با product_id) رو روی عکس کاربر اعمال می‌کنه و یه لینک عکس نتیجه (image_url) برمی‌گردونه."

### پ) `recommend_lipstick`
- Method: `POST`
- URL: `http://localhost:8000/analyze-skin-tone`
- Body: مثل بالا، فیلد باینری `file` = `{{ $('Webhook').item.binary.image }}`
- بدون پارامتر متنی از LLM.
- Description: "از روی عکس چهره‌ی کاربر، تن پوست رو تحلیل و ۳ محصول برتر کاتالوگ رو بر اساس delta-E رتبه‌بندی می‌کنه."

### ت) `live_tryon_info`
این یکی نیازی به HTTP نداره — یه **Tool منسوب به یه لینک ثابت**. ساده‌ترین راه: از نوع Code Tool استفاده کن که فقط این رو برمی‌گردونه:
```javascript
return { url: "https://your-domain.com/static/live_tryon.html" };
```
Description: "لینک صفحه‌ی لایو (امتحان با وبکم) رو برمی‌گردونه."

## ۴. استخراج لینک عکس + پاسخ نهایی

بعد از نود AI Agent، یه نود **Code** اضافه کن تا لینک عکس (اگه تولید شده بود) رو با regex از متن جواب Agent جدا کنی — این قابل‌اعتمادتر از اینه که فقط به این امید باشیم LLM لینک رو دقیق کپی کرده:

```javascript
const text = $input.first().json.output;
const match = text.match(/\/static\/results\/[a-f0-9]+\.png/);
return [{
  json: {
    reply: match ? text.replace(match[0], "").trim() : text,
    image_url: match ? match[0] : null,
  }
}];
```

نود آخر: **Respond to Webhook**
- Response Body: از همون خروجی نود Code (`{{ $json.reply }}` و `{{ $json.image_url }}`)
- اگه FastAPI و n8n روی دامنه‌های متفاوت‌ان، `image_url` نسبیه — یا باید توی همین Code node یه base URL جلوش اضافه کنی (`https://your-fastapi-domain.com` + مسیر)، یا FastAPI رو پشت همون دامنه‌ی n8n/reverse-proxy بذاری.

## چک‌لیست قبل از تست

- [ ] FastAPI روشنه و از طریق آدرسی که توی HTTP Request Toolها گذاشتی در دسترسه
- [ ] `AVALAI_API_KEY` (یا credential معادلش) توی n8n برای Chat Model ست شده
- [ ] CORS روی Webhook باز شده
- [ ] یه بار با Postman/curl مستقیم به خودِ webhook (بدون ویجت) تست کن قبل از وصل کردن فرانت
