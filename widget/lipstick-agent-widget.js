/*
  ویجت چت قابل‌جاسازی برای ایجنت رژ لب.

  استفاده (توی هر سایتی):
    <script
      src="https://your-domain.com/lipstick-agent-widget.js"
      data-webhook="https://your-n8n-domain.com/webhook/lipstick-agent"
      data-image-base="https://your-fastapi-domain.com"
      data-color="#c2185b"
      data-greeting="سلام! می‌خوای رژ لبی که دوست داری رو روی عکست امتحان کنی یا بگم کدوم بهت میاد؟"
    ></script>

  توضیح پارامترها:
    data-webhook     (اجباری) آدرس webhook در n8n که پیام‌ها به‌اونجا فرستاده می‌شن
    data-image-base  (اختیاری) اگه image_url که از سرور برمی‌گرده نسبیه (مثل
                     /static/results/xxx.png)، این base بهش اضافه می‌شه.
                     اگه سرورت خودِ لینک کامل رو می‌ده، لازم نیست این رو بذاری.
    data-color       (اختیاری) رنگ اصلی ویجت، پیش‌فرض یه صورتی ملایم
    data-greeting    (اختیاری) پیام خوش‌آمدگویی اول مکالمه

  🔧 نکته‌ی طراحی: از Shadow DOM استفاده شده تا استایل‌های این ویجت با
  استایل‌های سایت میزبان تداخل نکنه (نه اونا رو بهم بریزه، نه سایت
  میزبان استایل ویجت رو بهم بریزه) — این برای «هر سایتی خواست بذاره
  توی باتش» ضروریه.
*/

(function () {
  "use strict";

  var scriptTag = document.currentScript;
  var CONFIG = {
    webhookUrl: scriptTag.getAttribute("data-webhook"),
    imageBase: scriptTag.getAttribute("data-image-base") || "",
    color: scriptTag.getAttribute("data-color") || "#c2185b",
    greeting:
      scriptTag.getAttribute("data-greeting") ||
      "سلام! می‌تونم رژ لب روی عکست اعمال کنم یا بهت بگم کدوم رژ بهت میاد. چطور می‌تونم کمکت کنم؟",
  };

  if (!CONFIG.webhookUrl) {
    console.error("[lipstick-agent-widget] data-webhook تنظیم نشده — ویجت غیرفعاله.");
    return;
  }

  function getSessionId() {
    var key = "lla_session_id";
    var id = localStorage.getItem(key);
    if (!id) {
      id = "sess_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(key, id);
    }
    return id;
  }

  var host = document.createElement("div");
  host.setAttribute("id", "lipstick-agent-widget-host");
  document.body.appendChild(host);
  var shadow = host.attachShadow({ mode: "open" });

  var style = document.createElement("style");
  style.textContent =
    ":host{all:initial}" +
    "*{box-sizing:border-box;font-family:Tahoma,Arial,sans-serif}" +
    ".lla-launcher{position:fixed;bottom:20px;left:20px;width:60px;height:60px;border-radius:50%;" +
    "background:" + CONFIG.color + ";box-shadow:0 2px 10px rgba(0,0,0,.25);border:none;cursor:pointer;" +
    "display:flex;align-items:center;justify-content:center;z-index:999999}" +
    ".lla-launcher svg{width:28px;height:28px;fill:#fff}" +
    ".lla-panel{position:fixed;bottom:92px;left:20px;width:340px;max-width:92vw;height:480px;max-height:75vh;" +
    "background:#fff;border-radius:14px;box-shadow:0 4px 24px rgba(0,0,0,.2);display:none;flex-direction:column;" +
    "overflow:hidden;z-index:999999}" +
    ".lla-panel.open{display:flex}" +
    ".lla-header{background:" + CONFIG.color + ";color:#fff;padding:14px 16px;font-size:15px;font-weight:bold;" +
    "display:flex;justify-content:space-between;align-items:center}" +
    ".lla-close{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;line-height:1}" +
    ".lla-messages{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px;background:#f7f7f7}" +
    ".lla-msg{max-width:80%;padding:8px 12px;border-radius:12px;font-size:13px;line-height:1.5;white-space:pre-wrap}" +
    ".lla-msg.bot{background:#fff;border:1px solid #e2e2e2;align-self:flex-start;border-bottom-left-radius:2px}" +
    ".lla-msg.user{background:" + CONFIG.color + ";color:#fff;align-self:flex-end;border-bottom-right-radius:2px}" +
    ".lla-msg img{max-width:100%;border-radius:8px;margin-top:6px;display:block}" +
    ".lla-typing{align-self:flex-start;font-size:12px;color:#999;padding:4px 12px}" +
    ".lla-inputrow{border-top:1px solid #e5e5e5;padding:8px;display:flex;gap:6px;align-items:flex-end;background:#fff}" +
    ".lla-textinput{flex:1;border:1px solid #ddd;border-radius:10px;padding:8px 10px;font-size:13px;resize:none;" +
    "max-height:80px;min-height:36px}" +
    ".lla-iconbtn{background:none;border:none;cursor:pointer;padding:6px;color:#666;flex-shrink:0}" +
    ".lla-iconbtn svg{width:20px;height:20px;fill:currentColor}" +
    ".lla-sendbtn{background:" + CONFIG.color + ";border:none;border-radius:10px;color:#fff;padding:8px 14px;" +
    "cursor:pointer;font-size:13px;flex-shrink:0}" +
    ".lla-sendbtn:disabled{opacity:.5;cursor:default}" +
    ".lla-preview{display:flex;align-items:center;gap:6px;padding:6px 10px;font-size:12px;color:#555;" +
    "background:#f0f0f0;border-top:1px solid #e5e5e5}" +
    ".lla-preview img{width:32px;height:32px;object-fit:cover;border-radius:6px}" +
    ".lla-preview button{background:none;border:none;color:#c00;cursor:pointer;font-size:12px}";
  shadow.appendChild(style);

  var wrapper = document.createElement("div");
  wrapper.innerHTML =
    '<button class="lla-launcher" aria-label="باز کردن چت">' +
    '<svg viewBox="0 0 24 24"><path d="M12 3C6.5 3 2 6.8 2 11.5c0 2.6 1.4 4.9 3.6 6.5-.1.9-.5 2.3-1.4 3.6 0 0 2.3-.3 4.3-1.7 1 .3 2.1.5 3.5.5 5.5 0 10-3.8 10-8.9S17.5 3 12 3z"/></svg>' +
    "</button>" +
    '<div class="lla-panel">' +
    '<div class="lla-header"><span>مشاور رژ لب</span><button class="lla-close" aria-label="بستن">×</button></div>' +
    '<div class="lla-messages"></div>' +
    '<div class="lla-preview" style="display:none"></div>' +
    '<div class="lla-inputrow">' +
    '<button class="lla-iconbtn" data-action="attach" aria-label="پیوست عکس">' +
    '<svg viewBox="0 0 24 24"><path d="M16.5 6v10.5a4 4 0 01-8 0V5a2.5 2.5 0 015 0v9.5a1 1 0 01-2 0V6H10v8.5a2.5 2.5 0 005 0V5a4 4 0 00-8 0v11.5a5.5 5.5 0 0011 0V6h-1.5z"/></svg>' +
    "</button>" +
    '<input type="file" accept="image/*" style="display:none" class="lla-fileinput">' +
    '<textarea class="lla-textinput" rows="1" placeholder="پیامت رو بنویس..."></textarea>' +
    '<button class="lla-sendbtn">ارسال</button>' +
    "</div>" +
    "</div>";
  shadow.appendChild(wrapper);

  var launcher = shadow.querySelector(".lla-launcher");
  var panel = shadow.querySelector(".lla-panel");
  var closeBtn = shadow.querySelector(".lla-close");
  var messagesEl = shadow.querySelector(".lla-messages");
  var textInput = shadow.querySelector(".lla-textinput");
  var sendBtn = shadow.querySelector(".lla-sendbtn");
  var attachBtn = shadow.querySelector('[data-action="attach"]');
  var fileInput = shadow.querySelector(".lla-fileinput");
  var previewRow = shadow.querySelector(".lla-preview");

  var pendingFile = null;
  var greeted = false;

  launcher.addEventListener("click", function () {
    panel.classList.toggle("open");
    if (panel.classList.contains("open") && !greeted) {
      addMessage("bot", CONFIG.greeting);
      greeted = true;
    }
  });
  closeBtn.addEventListener("click", function () {
    panel.classList.remove("open");
  });

  attachBtn.addEventListener("click", function () {
    fileInput.click();
  });

  fileInput.addEventListener("change", function () {
    var f = fileInput.files[0];
    if (!f) return;
    pendingFile = f;
    var url = URL.createObjectURL(f);
    previewRow.style.display = "flex";
    previewRow.innerHTML =
      '<img src="' + url + '">' +
      "<span>عکس پیوست شد</span>" +
      '<button data-action="remove">حذف</button>';
    previewRow.querySelector('[data-action="remove"]').addEventListener("click", function () {
      pendingFile = null;
      fileInput.value = "";
      previewRow.style.display = "none";
      previewRow.innerHTML = "";
    });
  });

  function addMessage(role, text, imageUrl) {
    var el = document.createElement("div");
    el.className = "lla-msg " + role;
    var safeText = document.createElement("span");
    safeText.textContent = text || "";
    el.appendChild(safeText);
    if (imageUrl) {
      var img = document.createElement("img");
      img.src = imageUrl;
      el.appendChild(img);
    }
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addTyping() {
    var el = document.createElement("div");
    el.className = "lla-typing";
    el.textContent = "در حال تایپ...";
    el.setAttribute("data-typing", "1");
    messagesEl.appendChild(el);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return el;
  }

  function resolveImageUrl(url) {
    if (!url) return null;
    if (/^https?:\/\//i.test(url)) return url;
    return (CONFIG.imageBase || "") + url;
  }

  function sendMessage() {
    var text = textInput.value.trim();
    if (!text && !pendingFile) return;

    addMessage("user", text || (pendingFile ? "[عکس ارسال شد]" : ""), pendingFile ? URL.createObjectURL(pendingFile) : null);

    var formData = new FormData();
    formData.append("message", text);
    formData.append("session_id", getSessionId());
    if (pendingFile) formData.append("image", pendingFile);

    textInput.value = "";
    var attachedFile = pendingFile;
    pendingFile = null;
    fileInput.value = "";
    previewRow.style.display = "none";
    previewRow.innerHTML = "";
    sendBtn.disabled = true;

    var typingEl = addTyping();

    fetch(CONFIG.webhookUrl, { method: "POST", body: formData })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (data) {
        typingEl.remove();
        var reply = data.reply || data.output || "متاسفانه جوابی دریافت نشد.";
        var imageUrl = resolveImageUrl(data.image_url);
        addMessage("bot", reply, imageUrl);
      })
      .catch(function (err) {
        typingEl.remove();
        addMessage("bot", "مشکلی پیش اومد، لطفاً دوباره امتحان کن.");
        console.error("[lipstick-agent-widget]", err);
      })
      .finally(function () {
        sendBtn.disabled = false;
      });
  }

  sendBtn.addEventListener("click", sendMessage);
  textInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
})();
