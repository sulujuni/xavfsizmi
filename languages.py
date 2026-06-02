# All bot messages in 3 languages
# uz = Uzbek, ru = Russian, en = English

TEXTS = {
    "uz": {
        "choose_language": "🌐 Tilni tanlang / Choose language / Выберите язык:",
        "language_set": "✅ Til o'zbekchaga o'zgartirildi!",
        "start": (
            "👋 Salom, {name}! *Xavfsizmi? Bot*ga xush kelibsiz!\n\n"
            "🛡 Men sizga internetdagi xavflardan himoyalanishga yordam beraman.\n\n"
            "💬 *Iltimos, botdan to'liq foydalanish uchun quyidagi tugma orqali o'z tilingizni tanlang!*\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "⚙️ *MEN NIMALAR QILA OLAMAN?*\n\n"
            "🔗 *Havolalarni tekshirish*\n"
            "└ Istalgan URL yoki linkni yuboring → Ko'p qatlamli xavfsizlik tahlili\n\n"
            "📱 *APK fayllarni tekshirish*\n"
            "└ Istalgan 32MB dan oshmaydigan .APK faylni yuboring → xavfsizmi tekshiradi\n\n"
            "📸 *QR kodlarni tekshirish*\n"
            "└ QR kod rasmini yuboring → ichidagi URL xavfsizligini aniqlaydi\n\n"
            "🔐 *Email Breach*\n"
            "└ /breach email@mail.com → Ma'lumotlar sizib chiqqanini tekshirish\n"
        ),
        "checking": "🔄 Tekshirilmoqda...",
        "gsb_safe": "✅ *Google Safe Browsing:* Toza\n",
        "gsb_dangerous": "🛑 *Google Safe Browsing:* XAVFLI ({threat})\n",
        "gsb_error": "⚠️ *Google Safe Browsing:* Tekshirishda xatolik\n",
        "vt_safe": "✅ *VirusTotal:* Toza ({total} ta xavfsizlik vositasi tekshirdi)\n",
        "vt_suspicious": "⚠️ *VirusTotal:* {sus}/{total} tizim shubhali deb topdi.\n",
        "vt_malicious": "🛑 *VirusTotal:* {mal}/{total} ta antivirus xavf aniqladi!\n",
        "vt_error": "⚠️ *VirusTotal:* Cheklov yuzaga keldi (Muqobil tizimlar ishlatilmoqda)\n",
        "vt_new": "⏳ Havola birinchi marta yuborildi. Analiz qilinmoqda, qayta yuborib ko'ring.\n",
        "av_safe": "✅ *AlienVault OTX:* Toza\n",
        "av_malicious": "🛑 *AlienVault OTX:* Xavfli ({pulses} ta tahdid oqimi aniqlagan)\n",
        "us_safe": "✅ *Urlscan.io:* Sahifa tasdiqlandi (Xavf darajasi: {score}/100)\n",
        "us_malicious": "🛑 *Urlscan.io:* Zararli havola (Xavf darajasi: {score}/100)\n",
        "us_screenshot": "📸 [Sahifa ko'rinishi (Screenshot)]({url})\n",
        "domain_age": "🌐 *Domen yoshi:* {age} ({created})\n",
        "verdict_safe": "🟢 *Xulosa:* Bu havola xavfsiz ko'rinadi.",
        "verdict_dangerous": "🔴 *Xulosa:* DIQQAT! Ushbu havola xavfli bo'lishi mumkin!",
        "history_empty": "📭 Tarix bo'sh. Biror linkni tekshiring.",
        "history_title": "📋 *Oxirgi 10 ta tekshirilgan havolalar:*\n\n",
        "history_item": "• `{url}` — {status}\n",
        "report_sent": "✅ Hisobot yuborildi. Rahmat!",
        "report_invalid": "❌ To'liq URL yuboring. Misol: /report https://example.com",
        "stats_title": "📊 *Xavfsizmi? Bot Statistikasi*\n\n",
        "stats_text": "👥 Jami foydalanuvchilar: {users}\n⭐ Premium: {premium}\n🚨 Hisobotlar: {reports}\n\nFoydalanganingiz uchun rahmat! ❤️",
        "referral_link": (
            "👥 *Referral Dasturi*\n\n"
            "Do'stlarni taklif qiling va mukofot oling!\n\n"
            "Sizning taklif havolangiz:\n"
            "👉 `https://t.me/XavfsizmiBot?start={ref_code}`\n\n"
            "Siz jami {count} ta do'st taklif qildingiz."
        ),
        "breach_checking": "🔍 Email tekshirilmoqda...",
        "breach_compromised": "🚨 *EMAIL XAVF OSTIDA!*\n\n⚠️ `{email}` quyidagi {count} ta sizib chiqishda topildi:\n\n{breaches}\n\nParollarni zudlik bilan o'zgartiring!",
        "breach_safe": "✅ *EMAIL XAVFSIZ*\n\n`{email}` hech qanday ma'lumotlar sizib chiqishida topilmadi.",
        "breach_invalid": "❌ To'g'ri email yuboring. Misol: /breach user@example.com",
        "qr_invalid": "❌ QR kodni o'qib bo'lmadi. Tiniqroq rasm yuboring.",
        "limit_reached": "⚠️ Kunlik bepul limit tugadi ({limit}/{limit}).\n⭐ /premium sotib oling yoki do'stlarni /referral orqali taklif qiling!",
        "premium_title": "⭐ *Xavfsizmi? Premium*\n\nCheklovsiz havolalar va APK tahlili!\n\nNarxi: {stars} Telegram Stars\nSotib olish uchun quyidagi tugmani bosing:",
        "premium_buy": "⭐ Premium sotib olish ({stars} Stars)",
        "premium_success": "🎉 Tabriklaymiz! Siz muvaffaqiyatli Premium statusiga ega bo'ldingiz!",
        "group_welcome": "🔰 *Xavfsizmi? guruh himoyasi faollashtirildi!* Bot guruhdagi xavfli havolalarni avtomatik o'chiradi.",
        "group_malicious_removed": "🚨 *Xavfli havola o'chirildi!*\n👤 Foydalanuvchi: {user}\n⚠️ Sabab: Malicious Link.",
        "rate_limited": "⏳ Juda ko'p so'rov yuborildi. Biroz kuting.",
        "breach_premium_required": "⭐ *Premium imkoniyat!* Email ma'lumotlar sizib chiqishini tekshirish faqat premium foydalanuvchilar uchun ochiq.\n\nPremium sotib olish uchun /premium buyrug'idan foydalaning yoki Promokod kiriting: `/promo KOD_NOMI`",
        "promo_usage": "⌨️ *Promokoddan foydalanish:* `/promo KOD_NOMI`",
        "promo_invalid": "❌ Bunday promokod mavjud emas yoki xato kiritilgan.",
        "promo_already_used": "❌ Siz ushbu promokoddan foydalanib bo'lgansiz!",
        "promo_expired": "❌ Kechirasiz, ushbu bir martalik promokod allaqachon kimdir tomonidan ishlatilgan.",
        "promo_success_msg": "🎉 Tabriklaymiz! Promokod muvaffaqiyatli faollashtirildi. Sizga {days} kunlik Premium taqdim etildi!",
        "sub_required": "⚠️ *Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz shart!*\n\nPastdagi tugma orqali kanalga qo'shiling va keyin 'Tekshirish' tugmasini bosing.",
        "sub_button": "📢 Kanalga qo'shilish",
        "sub_check_btn": "🔄 Tekshirish",
        "sub_failed": "❌ Siz hali kanalga a'zo bo'lmadingiz! Iltimos, a'zo bo'lib qaytadan tekshirib ko'ring.",
        "stats_admin_only": "❌ Bu buyruq faqat bot adminlari uchun ochiq!",
        "feedback_usage": "⌨️ *Taklif va Shikoyatlar yo'llash:* `/feedback MATN` ko'rinishida yozing.\n\nMuhim: yuborgan xabaringiz to'g'ridan-to'g'ri bot ma'muriyatiga yetib boradi.",
        "feedback_received": "✅ Taklif yoki shikoyatingiz adminga muvaffaqiyatli yetkazildi. Fikringiz uchun rahmat!",
        "feedback_empty": "❌ Taklif yoki shikoyat matnini yozmadingiz. Misol: `/feedback Bot juda zo'r ishlamoqda!`",
        "feedback_admin_alert": "📩 *YANGI TAKLIF / SHIKOYAT!*\n\n👤 *Foydalanuvchi:* {name} (`{user_id}`)\n💬 *Xabar:* {text}",
        "report_usage": "⌨️ *Xavfli havola haqida xabar berish:* `/report https://example.com` ko'rinishida yuboring.",
        "breach_premium_required": (
        "⭐ *Premium yoki Referral kerak!*\n\n"
        "Email ma'lumotlar sizib chiqqanini tekshirish faqat Premium foydalanuvchilar uchun yoki "
        "kamida *1 ta do'stni taklif qilganlar* uchun ochiq.\n\n"
        "Sizda hozir: `{credits} ta bepul tekshirish imkoniyati` bor.\n\n"
        "💡 *Nima qilmoqchisiz?*\n"
        "1️⃣ Do'stlarni taklif qiling va bepul urinishga ega bo'ling: /referral\n"
        "2️⃣ To'liq va cheksiz Premium sotib oling: /premium"
        ),
    },
    
    "ru": {
        "choose_language": "🌐 Выберите язык / Choose language / Tilni tanlang:",
        "language_set": "✅ Язык изменен на русский!",
        "start": (
            "👋 Привет, {name}! Добро пожаловать в *Xavfsizmi? Bot*!\n\n"
            "🛡 Я помогу вам защититься от угроз в интернете.\n\n"
            "💬 *Пожалуйста, выберите язык с помощью кнопок ниже для полной настройки интерфейса!*\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "⚙️ *ЧТО Я УМЕЮ?*\n\n"
            "🔗 *Проверка ссылок*\n"
            "└ Отправьте любой URL → Многоуровневый анализ безопасности\n\n"
            "📱 *Проверка APK файлов*\n"
            "└ Любой .APK файл до 32MB → Проверка на вирусы\n\n"
            "📸 *Сканирование QR-кодов*\n"
            "└ Отправьте фото QR-кода → Проверим ссылку внутри него\n\n"
            "🔐 *Утечки Email*\n"
            "└ /breach email@mail.com → Проверка компрометации данных\n"
        ),
        "checking": "🔄 Проверяется...",
        "gsb_safe": "✅ *Google Safe Browsing:* Чисто\n",
        "gsb_dangerous": "🛑 *Google Safe Browsing:* ОПАСНО ({threat})\n",
        "gsb_error": "⚠️ *Google Safe Browsing:* Ошибка проверки\n",
        "vt_safe": "✅ *VirusTotal:* Чисто (Проверено {total} антивирусами)\n",
        "vt_suspicious": "⚠️ *VirusTotal:* {sus}/{total} антивирусов считают файл подозрительным.\n",
        "vt_malicious": "🛑 *VirusTotal:* Обнаружена угроза ({mal}/{total} антивирусов)!\n",
        "vt_error": "⚠️ *VirusTotal:* Лимит запросов исчерпан (Используются альтернативные базы)\n",
        "vt_new": "⏳ Ссылка отправлена впервые. Идет анализ, попробуйте позже.\n",
        "av_safe": "✅ *AlienVault OTX:* Чисто\n",
        "av_malicious": "🛑 *AlienVault OTX:* Вредоносный ресурс (Найден в {pulses} базах угроз)\n",
        "us_safe": "✅ *Urlscan.io:* Страница проверена (Индекс риска: {score}/100)\n",
        "us_malicious": "🛑 *Urlscan.io:* Вредоносная страница (Индекс риска: {score}/100)\n",
        "us_screenshot": "📸 [Скриншот страницы]({url})\n",
        "domain_age": "🌐 *Возраст домена:* {age} ({created})\n",
        "verdict_safe": "🟢 *Вердикт:* Ссылка безопасна.",
        "verdict_dangerous": "🔴 *Вердикт:* ВНИМАНИЕ! Ссылка может быть опасной!",
        "history_empty": "📭 История пуста. Сначала проверьте ссылку.",
        "history_title": "📋 *Последние 10 проверенных ссылок:*\n\n",
        "history_item": "• `{url}` — {status}\n",
        "report_sent": "✅ Жалоба отправлена. Спасибо!",
        "report_invalid": "❌ Отправьте полный URL. Пример: /report https://example.com",
        "stats_title": "📊 *Статистика Xavfsizmi? Bot*\n\n",
        "stats_text": "👥 Всего пользователей: {users}\n⭐ Премиум: {premium}\n🚨 Жалоб: {reports}\n\nСпасибо, что вы с нами! ❤️",
        "referral_link": (
            "👥 *Реферальная программа*\n\n"
            "Приглашайте друзей и получайте награды!\n\n"
            "Ваша реферальная ссылка:\n"
            "👉 `https://t.me/XavfsizmiBot?start={ref_code}`\n\n"
            "Вы пригласили {count} друзей."
        ),
        "breach_premium_required": (
            "⭐ *Требуется Премиум или Реферал!*\n\n"
            "Проверка утечки данных email доступна только для Премиум-пользователей или "
            "тех, кто пригласил как минимум *1 друга*.\n\n"
            "У вас сейчас: `{credits} свободных токенов`.\n\n"
            "💡 *Что вы хотите сделать?*\n"
            "1️⃣ Пригласите друзей и получите бесплатный токен: /referral\n"
            "2️⃣ Купить полный и безлимитный Премиум: /premium"
        ),
"phish_usage": "⌨️ *Использование симулятора фишинга:* Напишите `/phish` чтобы сгенерировать тестовую ссылку.",
"phish_created": (
    "🎣 *Ссылка для фишинг-теста успешно создана!*\n\n"
    "Скопируйте эту ссылку и отправьте её другу, чтобы проверить его бдительность:\n"
    "👉 `{link}`\n\n"
    "⚠️ Если ваш друг перейдет по ней, он получит предупреждение о безопасности, а вы получите уведомление!"
),
"phish_alert": "🚨 *Ваш друг попался!* Пользователь только что кликнул по вашей тестовой фишинг-ссылке. Ему стоит быть внимательнее!",
        "breach_checking": "🔍 Проверка email...",
        "breach_compromised": "🚨 *EMAIL СКОМПРОМЕТИРОВАН!*\n\n⚠️ `{email}` найден в {count} утечках данных:\n\n{breaches}\n\nСрочно измените пароли!",
        "breach_safe": "✅ *EMAIL В БЕЗОПАСНОСТИ*\n\n`{email}` не найден в базах известных утечек данных.",
        "breach_invalid": "❌ Введите корректный email. Пример: /breach user@example.com",
        "qr_invalid": "❌ Не удалось прочитать QR-код. Отправьте четкое фото.",
        "limit_reached": "⚠️ Дневной лимит исчерпан ({limit}/{limit}).\n⭐ Купите /premium или приглашайте друзей через /referral!",
        "premium_title": "⭐ *Xavfsizmi? Premium*\n\nБезлимитная проверка ссылок и APK файлов!\n\nСтоимость: {stars} Telegram Stars\nДля покупки нажмите кнопку ниже:",
        "premium_buy": "⭐ Купить Premium ({stars} Stars)",
        "premium_success": "🎉 Поздравляем! Вы успешно получили Премиум статус!",
        "group_welcome": "🔰 *Защита групп Xavfsizmi? включена!* Бот автоматически удаляет опасные ссылки в чате.",
        "group_malicious_removed": "🚨 *Опасная ссылка удалена!*\n👤 Пользователь: {user}\n⚠️ Причина: Вредоносная ссылка.",
        "rate_limited": "⏳ Слишком много запросов. Подождите немного.",
        "breach_premium_required": "⭐ *Премиум функция!* Проверка утечки данных электронной почты доступна только для Премиум пользователей.\n\nИспользуйте команду /premium для покупки или введите промокод: `/promo НАЗВАНИЕ_КОДА`",
        "promo_usage": "⌨️ *Использование промокода:* `/promo НАЗВАНИЕ_КОДА`",
        "promo_invalid": "❌ Такого промокода не существует или он введен неверно.",
        "promo_already_used": "❌ Вы уже использовали этот промокод!",
        "promo_expired": "❌ К сожалению, этот одноразовый промокод уже кем-то активирован.",
        "promo_success_msg": "🎉 Поздравляем! Промокод успешно активирован. Вам предоставлено {days} дней Премиум доступа!",
        "sub_required": "⚠️ *Для использования бота вы должны подписаться на наш канал!*\n\nВступите в канал по кнопке ниже и нажмите 'Проверить'.",
        "sub_button": "📢 Подписаться на канал",
        "sub_check_btn": "🔄 Проверить",
        "sub_failed": "❌ Вы еще не подписались на канал! Пожалуйста, подпишитесь и проверьте снова.",
        "stats_admin_only": "❌ Эта команда доступна только администраторам бота!",
        "feedback_usage": "⌨️ *Отправка предложений и жалоб:* Напишите в формате `/feedback ТЕКСТ`.\n\nВажно: ваше сообщение будет отправлено напрямую администрации.",
        "feedback_received": "✅ Ваше предложение или жалоба успешно доставлены администратору. Спасибо за отзыв!",
        "feedback_empty": "❌ Вы не написали текст предложения или жалобы. Пример: `/feedback Бот работает отлично!`",
        "feedback_admin_alert": "📩 *НОВОЕ ПРЕДЛОЖЕНИЕ / ЖАЛОБА!*\n\n👤 *Пользователь:* {name} (`{user_id}`)\n💬 *Текст:* {text}",
        "report_usage": "⌨️ *Сообщить об опасной ссылке:* Отправьте в формате `/report https://example.com`."
    },
    "en": {
        "choose_language": "🌐 Choose language / Выберите язык / Tilni tanlang:",
        "language_set": "✅ Language changed to English!",
        "start": (
            "👋 Hello, {name}! Welcome to *Xavfsizmi? Bot*!\n\n"
            "🛡 I am here to safeguard your navigation over the internet.\n\n"
            "💬 *Please use the inline menu below to configure your default language interface!*\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "⚙️ *WHAT CAN I DO?*\n\n"
            "🔗 *URL Link Scanning*\n"
            "└ Send any link → Deep multi-layer reputation checks\n\n"
            "📱 *APK Android Scanning*\n"
            "└ Upload any .APK (max 32MB) → Automated malware sandbox sweep\n\n"
            "📸 *QR Code Reading*\n"
            "└ Submit a clear picture of any QR → Scan extracted targets\n\n"
            "🔐 *Data Breach Tracking*\n"
            "└ /breach email@mail.com → Scan global account exposures\n"
        ),
        "checking": "🔄 Scanning target destination...",
        "gsb_safe": "✅ *Google Safe Browsing:* Clean\n",
        "gsb_dangerous": "🛑 *Google Safe Browsing:* DANGEROUS ({threat})\n",
        "gsb_error": "⚠️ *Google Safe Browsing:* Lookup Error\n",
        "vt_safe": "✅ *VirusTotal:* Clean ({total} engines checked)\n",
        "vt_suspicious": "⚠️ *VirusTotal:* {sus}/{total} engines flagged as suspicious.\n",
        "vt_malicious": "🛑 *VirusTotal:* {mal}/{total} engines detected severe threats!\n",
        "vt_error": "⚠️ *VirusTotal:* Capacity Rate-Locked (Using independent safety clusters)\n",
        "vt_new": "⏳ First-time submitted URL. Analyzing threat matrix, query back shortly.\n",
        "av_safe": "✅ *AlienVault OTX:* Clean\n",
        "av_malicious": "🛑 *AlienVault OTX:* Malicious (Identified across {pulses} active feeds)\n",
        "us_safe": "✅ *Urlscan.io:* Document Verified (Risk Score: {score}/100)\n",
        "us_malicious": "🛑 *Urlscan.io:* Malicious Target (Risk Score: {score}/100)\n",
        "us_screenshot": "📸 [Live Page Preview Screenshot]({url})\n",
        "domain_age": "🌐 *Domain Age:* {age} ({created})\n",
        "verdict_safe": "🟢 *Verdict:* The destination link appears completely safe.",
        "verdict_dangerous": "🔴 *Verdict:* WARNING! Dangerous payload signatures found!",
        "history_empty": "📭 History is empty. Check a link first.",
        "history_title": "📋 *Your last 10 checked links:*\n\n",
        "history_item": "• `{url}` — {status}\n",
        "report_sent": "✅ Report recorded. Thank you!",
        "report_invalid": "❌ Please issue a valid address format. Example: /report https://example.com",
        "stats_title": "📊 *Xavfsizmi? Global Statistics*\n\n",
        "stats_text": "👥 Total Users: {users}\n⭐ Premium Subscribers: {premium}\n🚨 Incident Reports: {reports}\n\nThank you for scaling safety! ❤️",
        "referral_link": (
            "👥 *Referral Program*\n\n"
            "Share Xavfsizmi? and unlock premium benefits!\n\n"
            "Your custom tracking link:\n"
            "👉 `https://t.me/XavfsizmiBot?start={ref_code}`\n\n"
            "Registered invitations: {count} friends."
        ),
        "breach_premium_required": (
            "⭐ *Premium or Referral Required!*\n\n"
            "Email breach scanning is restricted to Premium subscribers or users who have "
            "invitation credits by *referring at least 1 friend*.\n\n"
            "Your current balance: `{credits} free scan tokens`.\n\n"
            "💡 *What would you like to do?*\n"
            "1️⃣ Invite friends to earn free dynamic tokens: /referral\n"
            "2️⃣ Unlock permanent access: /premium"
        ),
        "breach_checking": "🔍 Inspecting email logs...",
        "breach_compromised": "🚨 *EMAIL DISCOVERED IN DATA BREACHES!*\n\n⚠️ `{email}` exposed inside {count} known breaches:\n\n{breaches}\n\nUpdate your credentials immediately!",
        "breach_safe": "✅ *EMAIL ACCOUNT SECURE*\n\n`{email}` was not found in any indexed global leakages.",
        "breach_invalid": "❌ Invalid layout. Example: /breach user@example.com",
        "qr_invalid": "❌ Could not decode matrix. Ensure picture has sharp contrast.",
        "limit_reached": "⚠️ Daily lookups exhausted ({limit}/{limit}).\n⭐ Upgrade via /premium or claim usage credits via /referral!",
        "premium_title": "⭐ *Xavfsizmi? Premium Core*\n\nUnlimited links and system sandbox operations!\n\nValue: {stars} Telegram Stars\nConfirm checkout beneath:",
        "premium_buy": "⭐ Buy Premium ({stars} Stars)",
        "premium_success": "🎉 Access Authorized! Welcome to Xavfsizmi? Premium Tier!",
        "group_welcome": "🔰 *Xavfsizmi? group armor active!* Auto-purging links containing unsafe structures.",
        "group_malicious_removed": "🚨 *Malicious Link Extracted!*\n👤 Identity: {user}\n⚠️ Reason: Failed safety profile criteria.",
        "rate_limited": "⏳ Flood warning. Calm down your inputs.",
        "breach_premium_required": "⭐ *Premium Feature!* Email breach scanning is restricted to Premium subscribers.\n\nUse /premium to upgrade or claim via a promotional code: `/promo CODE_NAME`",
        "promo_usage": "⌨️ *Promocode usage syntax:* `/promo CODE_NAME`",
        "promo_invalid": "❌ This promotional code does not exist or is structurally invalid.",
        "promo_already_used": "❌ You have already redeemed this promotional code!",
        "promo_expired": "❌ Too late! This single-use promotional code has already been redeemed by another account.",
        "promo_success_msg": "🎉 Success! Promotional code activated. You have been granted {days} days of Premium authorization!",
        "sub_required": "⚠️ *You must subscribe to our channel to use this bot!*\n\nJoin the channel using the button below and then click 'Verify'.",
        "sub_button": "📢 Join Channel",
        "sub_check_btn": "🔄 Verify Sub",
        "sub_failed": "❌ You haven't joined the channel yet! Please subscribe and try verifying again.",
        "stats_admin_only": "❌ This command is only available for bot administrators!",
        "feedback_usage": "⌨️ *Send Suggestions & Complaints:* Write in format `/feedback TEXT`.\n\nImportant: your message will be forwarded directly to the admin team.",
        "feedback_received": "✅ Your feedback has been successfully delivered to the admin. Thank you!",
        "feedback_empty": "❌ You didn't provide any text. Example: `/feedback Great bot, thank you!`",
        "feedback_admin_alert": "📩 *NEW FEEDBACK / COMPLAINT!*\n\n👤 *User:* {name} (`{user_id}`)\n💬 *Message:* {text}",
        "report_usage": "⌨️ *Report a dangerous link:* Send in format `/report https://example.com`."
    }
}

def t(lang: str, key: str, **kwargs) -> str:
    """Helper function to fetch localized messages safely for private chats."""
    lang_dict = TEXTS.get(lang, TEXTS["uz"])
    text_template = lang_dict.get(key, TEXTS["uz"].get(key, f"[{key}]"))
    try:
        return text_template.format(**kwargs)
    except (KeyError, IndexError):
        return text_template


def gt(lang: str, key: str, **kwargs) -> str:
    """Group text — same as t() but used for group messages to clarify context."""
    return t(lang, key, **kwargs)


def at(lang: str, key: str, **kwargs) -> str:
    """APK/Auto text — localized messages for APK and auto-scan results in groups."""
    return t(lang, key, **kwargs)


def pt(lang: str, key: str, **kwargs) -> str:
    """Premium text — localized messages for payment/premium related actions."""
    return t(lang, key, **kwargs)


def nf(lang: str, key: str, **kwargs) -> str:
    """Notification text — localized messages for notifications."""
    return t(lang, key, **kwargs)


# ─── GROUP APK/QR SCAN TEXT KEYS ─────────────────────────────────────────────

for _lang in ["uz", "ru", "en"]:
    if "scanning" not in TEXTS[_lang]:
        TEXTS["uz"]["scanning"] = "🔍 *APK fayl tahlil qilinmoqda...*"
        TEXTS["ru"]["scanning"] = "🔍 *Анализ APK файла...*"
        TEXTS["en"]["scanning"] = "🔍 *Scanning APK file...*"

    if "too_large" not in TEXTS[_lang]:
        TEXTS["uz"]["too_large"] = "❌ APK fayl hajmi juda katta. Maksimal limit 32 MB."
        TEXTS["ru"]["too_large"] = "❌ Файл слишком большой. Максимальный размер — 32 МБ."
        TEXTS["en"]["too_large"] = "❌ File too large. Maximum size is 32 MB."

    if "timeout" not in TEXTS[_lang]:
        TEXTS["uz"]["timeout"] = "⏳ VirusTotal javob bermadi. Keyinroq urinib ko'ring."
        TEXTS["ru"]["timeout"] = "⏳ VirusTotal не ответил. Попробуйте позже."
        TEXTS["en"]["timeout"] = "⏳ VirusTotal timed out. Try again later."

    if "error" not in TEXTS[_lang]:
        TEXTS["uz"]["error"] = "❌ Tekshirishda xatolik yuz berdi."
        TEXTS["ru"]["error"] = "❌ Произошла ошибка при проверке."
        TEXTS["en"]["error"] = "❌ An error occurred during scanning."

    if "suspicious" not in TEXTS[_lang]:
        TEXTS["uz"]["suspicious"] = "⚠️ *Shubhali APK!*\n📱 Fayl: `{name}`\nShubhali: `{sus}/{total}`"
        TEXTS["ru"]["suspicious"] = "⚠️ *Подозрительный APK!*\n📱 Файл: `{name}`\nПодозрительный: `{sus}/{total}`"
        TEXTS["en"]["suspicious"] = "⚠️ *Suspicious APK!*\n📱 File: `{name}`\nSuspicious: `{sus}/{total}`"

    if "safe" not in TEXTS[_lang]:
        TEXTS["uz"]["safe"] = "✅ *Xavfsiz APK!*\n📱 Fayl: `{name}`\n{total} ta dvigatel tekshirdi — xavf topilmadi."
        TEXTS["ru"]["safe"] = "✅ *Безопасный APK!*\n📱 Файл: `{name}`\n{total} антивирусов проверили — угроз нет."
        TEXTS["en"]["safe"] = "✅ *Safe APK!*\n📱 File: `{name}`\n{total} engines checked — no threats found."


# ─── FIX: PHISH KEYS & SECRETARY INFO IN START ───────────────────────────────

# Ensure phish keys exist in all languages
if "phish_created" not in TEXTS["uz"]:
    TEXTS["uz"]["phish_created"] = (
        "🎣 *Fishing test havolasi yaratildi!*\n\n"
        "Ushbu havolani do\'stingizga yuboring:\n"
        "👉 `{link}`\n\n"
        "⚠️ Do\'stingiz bosgan zahoti ogohlantirish sahifasiga o\'tkaziladi va siz xabar olasiz!"
    )
    TEXTS["uz"]["phish_alert"] = (
        "🔍 *Do\'stingiz tuzog\'ingizga tushdi!* "
        "Test havolangizni bosdi. Kiberxavfsizlik bilimini oshirishi kerak!"
    )

if "phish_created" not in TEXTS["en"]:
    TEXTS["en"]["phish_created"] = (
        "🎣 *Phishing test link created!*\n\n"
        "Send this link to your friend:\n"
        "👉 `{link}`\n\n"
        "⚠️ When they click it they get a warning and you\'ll be notified!"
    )
    TEXTS["en"]["phish_alert"] = (
        "🔍 *Your friend fell for the test!* "
        "They clicked your phishing test link. They need cybersecurity training!"
    )

# Add secretary mode info to ALL start messages
_SEC_UZ = (
    "\n🤖 *Secretary Rejimi* ⭐\n"
    "└ Telegram Business → Bot kiruvchi xabarlaringizni skanerlaydi\n"
    "└ Yoqish: Telegram Settings → Business → Chatbots → Bu botni qo\'shing\n"
)
_SEC_RU = (
    "\n🤖 *Режим Секретаря* ⭐\n"
    "└ Telegram Business → Бот сканирует входящие сообщения\n"
    "└ Включить: Telegram Settings → Business → Chatbots → Добавить бота\n"
)
_SEC_EN = (
    "\n🤖 *Secretary Mode* ⭐\n"
    "└ Telegram Business → Bot scans your incoming messages\n"
    "└ Enable: Telegram Settings → Business → Chatbots → Add this bot\n"
)

# Add to start messages if not already there
for lang, sec in [("uz", _SEC_UZ), ("ru", _SEC_RU), ("en", _SEC_EN)]:
    if "Secretary" not in TEXTS[lang].get("start", "") and "Секретар" not in TEXTS[lang].get("start", ""):
        current = TEXTS[lang].get("start", "")
        # Insert before the footer (before the ⚡ or ━ line near end)
        if "━━━━━━━━━━━━━━━━\n⚡" in current:
            TEXTS[lang]["start"] = current.replace(
                "━━━━━━━━━━━━━━━━\n⚡",
                sec + "━━━━━━━━━━━━━━━━\n⚡"
            )
