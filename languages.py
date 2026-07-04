# All bot messages in 3 languages
# uz = Uzbek, ru = Russian, en = English

TEXTS = {
    "uz": {
        "choose_language": "🌐 Tilni tanlang / Choose language / Выберите язык:",
        "language_set": "✅ Til o'zbekchaga o'zgartirildi!",
        "start": (
            "👋 Salom, {name}!\n\n"
            "🛡 *Xavfsizmi?* — sizning shaxsiy kiberxavfsizlik yordamchingiz.\n\n"
            "Menga havola, fayl yoki QR kod yuboring — xavfsizligini tekshirib beraman.\n\n"
            "━━━ *Buyruqlar* ━━━\n"
            "/help — Barcha buyruqlar\n"
            "/breach — Email/parol tekshirish\n"
            "/ask — AI ga savol berish\n"
            "/analyze — Shubhali xabarni tahlil qilish\n"
            "/scammer — Akkaunt tekshirish\n"
            "/darkweb — Dark web tekshiruvi\n"
            "/monitor — Email monitoring (Premium)\n"
            "/phish — Fishing simulyatori\n"
            "/referral — Do'stlarni taklif qilish\n"
            "/top — Liderlar jadvali\n"
            "/tips — Kunlik maslahatlar\n"
            "/premium — Premium olish\n"
            "/history — Tekshiruvlar tarixi\n"
            "/language — Tilni o'zgartirish\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "📊 Kunlik limit: {limit} ta bepul tekshiruv\n"
            "⭐ Cheksiz → /premium\n"
            "🤖 Secretary rejimi: Telegram → Business → Chatbots"
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
            "👋 Привет, {name}!\n\n"
            "🛡 *Xavfsizmi?* — ваш личный помощник по кибербезопасности.\n\n"
            "Отправьте мне ссылку, файл или QR-код — проверю на безопасность.\n\n"
            "━━━ *Команды* ━━━\n"
            "/help — Все команды\n"
            "/breach — Проверка email/пароля\n"
            "/ask — Задать вопрос AI\n"
            "/analyze — Анализ подозрительного сообщения\n"
            "/scammer — Проверка аккаунта\n"
            "/darkweb — Проверка в dark web\n"
            "/monitor — Мониторинг email (Премиум)\n"
            "/phish — Симулятор фишинга\n"
            "/referral — Пригласить друзей\n"
            "/top — Таблица лидеров\n"
            "/tips — Ежедневные советы\n"
            "/premium — Купить Премиум\n"
            "/history — История проверок\n"
            "/language — Сменить язык\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "📊 Дневной лимит: {limit} бесплатных проверок\n"
            "⭐ Безлимит → /premium\n"
            "🤖 Режим секретаря: Telegram → Business → Chatbots"
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
            "👋 Hi, {name}!\n\n"
            "🛡 *Xavfsizmi?* — your personal cybersecurity assistant.\n\n"
            "Send me a link, file, or QR code — I'll check if it's safe.\n\n"
            "━━━ *Commands* ━━━\n"
            "/help — All commands\n"
            "/breach — Check email/password leaks\n"
            "/ask — Ask AI a question\n"
            "/analyze — Analyze a suspicious message\n"
            "/scammer — Check an account\n"
            "/darkweb — Dark web search\n"
            "/monitor — Email monitoring (Premium)\n"
            "/phish — Phishing simulator\n"
            "/referral — Invite friends\n"
            "/top — Leaderboard\n"
            "/tips — Daily security tips\n"
            "/premium — Get Premium\n"
            "/history — Check history\n"
            "/language — Change language\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "📊 Daily limit: {limit} free checks\n"
            "⭐ Unlimited → /premium\n"
            "🤖 Secretary mode: Telegram → Business → Chatbots"
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
    "🔍 *Do\'stingiz ({name}) tuzog\'ingizga tushdi!* "
    "Test havolangizni bosdi. Kiberxavfsizlik bilimini oshirishi kerak!"
)

if "phish_created" not in TEXTS["ru"]:
    TEXTS["ru"]["phish_created"] = (
        "🎣 *Ссылка для фишинг-теста создана!*\n\n"
        "Отправьте эту ссылку другу:\n"
        "👉 `{link}`\n\n"
        "⚠️ Когда друг нажмёт — получит предупреждение, а вы — уведомление!"
    )
TEXTS["ru"]["phish_alert"] = (
    "🔍 *Ваш друг ({name}) попался!* "
    "Он кликнул по вашей тестовой фишинг-ссылке. Ему стоит быть внимательнее!"
)

if "phish_created" not in TEXTS["en"]:
    TEXTS["en"]["phish_created"] = (
        "🎣 *Phishing test link created!*\n\n"
        "Send this link to your friend:\n"
        "👉 `{link}`\n\n"
        "⚠️ When they click it they get a warning and you\'ll be notified!"
    )
TEXTS["en"]["phish_alert"] = (
    "🔍 *Your friend ({name}) fell for the test!* "
    "They clicked your phishing test link. They need cybersecurity training!"
)



# ─── MISSING KEYS: dangerous_deleted, dangerous_no_permission, phish_usage ───

TEXTS["uz"]["dangerous_deleted"] = "🚨 *Xavfli havola o'chirildi!*\n👤 {mention} yuborgan `{url}` havolasi xavfli deb topildi ({engines} ta antivirus).\n❌ Xabar o'chirildi."
TEXTS["ru"]["dangerous_deleted"] = "🚨 *Опасная ссылка удалена!*\n👤 Ссылка `{url}` от {mention} признана опасной ({engines} антивирусов).\n❌ Сообщение удалено."
TEXTS["en"]["dangerous_deleted"] = "🚨 *Dangerous link deleted!*\n👤 Link `{url}` sent by {mention} was flagged as malicious ({engines} engines).\n❌ Message removed."

TEXTS["uz"]["dangerous_no_permission"] = "⚠️ {mention} yuborgan `{url}` havolasi xavfli! Lekin botda o'chirish huquqi yo'q. Admin, iltimos xabarni o'chiring!"
TEXTS["ru"]["dangerous_no_permission"] = "⚠️ Ссылка `{url}` от {mention} опасна! Но у бота нет прав на удаление. Админ, удалите сообщение!"
TEXTS["en"]["dangerous_no_permission"] = "⚠️ Link `{url}` from {mention} is dangerous! But bot lacks delete permission. Admin, please remove the message!"

TEXTS["uz"]["phish_usage"] = "⌨️ *Fishing simulyatoridan foydalanish:* `/phish` buyrug'ini yozing va do'stlaringizni sinab ko'ring."
TEXTS["en"]["phish_usage"] = "⌨️ *Phishing simulator usage:* Type `/phish` to generate a test message for your friends."



# ─── PREMIUM COMMAND TEXTS (all languages) ────────────────────────────────────

TEXTS["uz"]["premium_already_active"] = "⭐ Sizda allaqachon Premium status faol!"
TEXTS["ru"]["premium_already_active"] = "⭐ У вас уже активен Премиум статус!"
TEXTS["en"]["premium_already_active"] = "⭐ You already have active Premium status!"

TEXTS["uz"]["premium_info"] = (
    "⚡ *SafeLink Premium obunasi!*\n\n"
    "Premium afzalliklari:\n"
    "• Cheksiz tekshirish (URL + APK + QR)\n"
    "• To'liq /breach ma'lumotlar bazasi\n"
    "• Reklamasiz va yuqori tezlik\n\n"
    "💳 *To'lov usulini tanlang:*"
)
TEXTS["ru"]["premium_info"] = (
    "⚡ *SafeLink Premium подписка!*\n\n"
    "Преимущества Premium:\n"
    "• Безлимитные проверки (URL + APK + QR)\n"
    "• Полный доступ к /breach базе утечек\n"
    "• Без рекламы и высокая скорость\n\n"
    "💳 *Выберите способ оплаты:*"
)
TEXTS["en"]["premium_info"] = (
    "⚡ *SafeLink Premium Subscription!*\n\n"
    "Premium benefits:\n"
    "• Unlimited checks (URL + APK + QR)\n"
    "• Full /breach leak database access\n"
    "• No ads and high-speed analysis\n\n"
    "💳 *Choose payment method:*"
)

TEXTS["uz"]["premium_promo_hint"] = (
    "🎟 *Promokodingiz bormi?*\n\n"
    "Agar sizda promokod bo'lsa, uni quyidagicha faollashtiring:\n"
    "👉 `/promo KODINGIZ`\n\n"
    "Misol: `/promo FREE30`"
)
TEXTS["ru"]["premium_promo_hint"] = (
    "🎟 *Есть промокод?*\n\n"
    "Если у вас есть промокод, активируйте его так:\n"
    "👉 `/promo ВАШКОД`\n\n"
    "Пример: `/promo FREE30`"
)
TEXTS["en"]["premium_promo_hint"] = (
    "🎟 *Have a promo code?*\n\n"
    "If you have a promo code, activate it like this:\n"
    "👉 `/promo YOURCODE`\n\n"
    "Example: `/promo FREE30`"
)



# ─── NEW FEATURE TEXT KEYS ────────────────────────────────────────────────────

# Bulk check
TEXTS["uz"]["bulk_usage"] = "📋 *Bulk Tekshiruv:*\n\nBir nechta havolani tekshirish uchun:\n`/bulk https://link1.com\nhttps://link2.com`\n\nHar bir qatorga bitta havola yozing."
TEXTS["ru"]["bulk_usage"] = "📋 *Массовая Проверка:*\n\nДля проверки нескольких ссылок:\n`/bulk https://link1.com\nhttps://link2.com`\n\nОдна ссылка на строку."
TEXTS["en"]["bulk_usage"] = "📋 *Bulk Check:*\n\nTo check multiple links:\n`/bulk https://link1.com\nhttps://link2.com`\n\nOne link per line."

# Expand
TEXTS["uz"]["expand_usage"] = "🔀 *URL Kengaytirish:*\n\n`/expand https://bit.ly/xxxxx`\n\nQisqa havolaning asl manzilini ko'rsatadi."
TEXTS["ru"]["expand_usage"] = "🔀 *Развернуть URL:*\n\n`/expand https://bit.ly/xxxxx`\n\nПоказывает реальный адрес короткой ссылки."
TEXTS["en"]["expand_usage"] = "🔀 *Expand URL:*\n\n`/expand https://bit.ly/xxxxx`\n\nReveals the real destination of a short link."

TEXTS["uz"]["expand_no_redirect"] = "✅ `{url}` — hech qanday yo'naltirish yo'q. To'g'ridan-to'g'ri ochiladi."
TEXTS["ru"]["expand_no_redirect"] = "✅ `{url}` — нет перенаправлений. Открывается напрямую."
TEXTS["en"]["expand_no_redirect"] = "✅ `{url}` — no redirects. Opens directly."

# SSL
TEXTS["uz"]["ssl_usage"] = "🔒 *SSL Sertifikat Tekshiruvi:*\n\n`/ssl example.com`\n\nSaytning xavfsizlik sertifikatini tekshiradi."
TEXTS["ru"]["ssl_usage"] = "🔒 *Проверка SSL Сертификата:*\n\n`/ssl example.com`\n\nПроверяет сертификат безопасности сайта."
TEXTS["en"]["ssl_usage"] = "🔒 *SSL Certificate Check:*\n\n`/ssl example.com`\n\nChecks the site's security certificate."

# Redirect
TEXTS["uz"]["redirect_usage"] = "🔗 *Redirect Zanjiri:*\n\n`/redirect https://example.com`\n\nHavola qayerga olib borishini ko'rsatadi."
TEXTS["ru"]["redirect_usage"] = "🔗 *Цепочка Редиректов:*\n\n`/redirect https://example.com`\n\nПоказывает куда ведёт ссылка."
TEXTS["en"]["redirect_usage"] = "🔗 *Redirect Chain:*\n\n`/redirect https://example.com`\n\nShows where a link actually leads."

# Typo
TEXTS["uz"]["typo_usage"] = "🔤 *Typosquatting Tekshiruvi:*\n\n`/typo gooogle.com`\n\nDomen nomi mashhur saytlarga o'xshash emasligini tekshiradi."
TEXTS["ru"]["typo_usage"] = "🔤 *Проверка Тайпосквоттинга:*\n\n`/typo gooogle.com`\n\nПроверяет не является ли домен подделкой."
TEXTS["en"]["typo_usage"] = "🔤 *Typosquatting Check:*\n\n`/typo gooogle.com`\n\nChecks if a domain is a fake version of a popular site."

# Scammer
TEXTS["uz"]["scammer_usage"] = "👤 *Skammer Tekshiruvi:*\n\n`/scammer @username`\n\nFoydalanuvchi skammer sifatida xabar qilinganmi tekshiradi."
TEXTS["ru"]["scammer_usage"] = "👤 *Проверка Скаммера:*\n\n`/scammer @username`\n\nПроверяет был ли пользователь отмечен как мошенник."
TEXTS["en"]["scammer_usage"] = "👤 *Scammer Check:*\n\n`/scammer @username`\n\nChecks if a user has been reported as a scammer."

# Privacy
TEXTS["uz"]["privacy_usage"] = "🔏 *Maxfiylik Tahlili:*\n\n`/privacy https://instagram.com/username`\n\nProfildagi ochiq ma'lumotlarni tahlil qiladi."
TEXTS["ru"]["privacy_usage"] = "🔏 *Анализ Приватности:*\n\n`/privacy https://instagram.com/username`\n\nАнализирует публичную информацию профиля."
TEXTS["en"]["privacy_usage"] = "🔏 *Privacy Analysis:*\n\n`/privacy https://instagram.com/username`\n\nAnalyzes public information exposure of a profile."

# Tips
TEXTS["uz"]["tips_enabled"] = "✅ Kunlik xavfsizlik maslahatlari YOQILDI! Har kuni bir ta maslahat olasiz."
TEXTS["ru"]["tips_enabled"] = "✅ Ежедневные советы по безопасности ВКЛЮЧЕНЫ! Вы будете получать совет каждый день."
TEXTS["en"]["tips_enabled"] = "✅ Daily security tips ENABLED! You'll receive a tip every day."

TEXTS["uz"]["tips_disabled"] = "❌ Kunlik maslahatlar O'CHIRILDI. Qayta yoqish: `/tips on`"
TEXTS["ru"]["tips_disabled"] = "❌ Ежедневные советы ОТКЛЮЧЕНЫ. Включить: `/tips on`"
TEXTS["en"]["tips_disabled"] = "❌ Daily tips DISABLED. Re-enable: `/tips on`"

# Leaderboard
TEXTS["uz"]["leaderboard_title"] = "🏆 *Referral Liderlar Jadvali (Oylik):*"
TEXTS["ru"]["leaderboard_title"] = "🏆 *Таблица Лидеров Рефералов (Месяц):*"
TEXTS["en"]["leaderboard_title"] = "🏆 *Referral Leaderboard (Monthly):*"

TEXTS["uz"]["leaderboard_empty"] = "📭 Hozircha hech kim do'st taklif qilmagan. Birinchi bo'ling! /referral"
TEXTS["ru"]["leaderboard_empty"] = "📭 Пока никто не пригласил друзей. Будьте первым! /referral"
TEXTS["en"]["leaderboard_empty"] = "📭 No referrals yet. Be the first! /referral"

TEXTS["uz"]["leaderboard_footer"] = "⭐ Top 3 har oy oxirida 30 kunlik bepul Premium oladi!"
TEXTS["ru"]["leaderboard_footer"] = "⭐ Топ 3 получают 30 дней бесплатного Премиума в конце месяца!"
TEXTS["en"]["leaderboard_footer"] = "⭐ Top 3 get 30 days free Premium at the end of each month!"



# ─── OVERRIDE: SHORT START MESSAGE + HELP COMMAND ─────────────────────────────

# ─── HELP MESSAGE (detailed) ─────────────────────────────────────────────────

TEXTS["uz"]["help_message"] = (
    "📖 *Xavfsizmi? Bot — Barcha Buyruqlar:*\n\n"
    "━━━ *Asosiy Tekshiruvlar* ━━━\n"
    "🔗 *Havola yuborish* — URL ni ko'p qatlamli tahlil qiladi (Trust Score, SSL, typosquatting, redirect zanjiri)\n"
    "📱 *APK fayl yuborish* — VirusTotal orqali skanerlaydi (ruxsatlar, tarmoq, sandbox)\n"
    "📸 *QR kod rasmi* — ichidagi URL ni topib tekshiradi\n\n"
    "━━━ *Buyruqlar* ━━━\n"
    "/breach — Email ma'lumotlar sizib chiqqanini tekshirish\n"
    "/scammer @username — Akkaunt skammer emasligini tekshirish\n"
    "/privacy https://... — Profil maxfiylik tahlili\n"
    "/phish — Do'stlaringizni fishing testi bilan sinash\n"
    "/tips — Kunlik xavfsizlik maslahatlari (on/off)\n"
    "/top — Referral liderlar jadvali\n"
    "/referral — Do'stlarni taklif qilish havolasi\n"
    "/premium — Premium xarid / Promokod\n"
    "/history — Oxirgi tekshiruvlar tarixi\n"
    "/report https://... — Xavfli link haqida xabar\n"
    "/feedback matn — Taklif/shikoyat yuborish\n"
    "/language — Tilni o'zgartirish\n\n"
    "━━━ *Avtomatik Tahlillar* ━━━\n"
    "Har bir havola tekshirilganda avtomatik:\n"
    "• 🎯 Trust Score (0-100)\n"
    "• 🔒 SSL sertifikat holati\n"
    "• 🔤 Typosquatting aniqlash\n"
    "• 🔀 Qisqa havola kengaytirish\n"
    "• 🔗 Redirect zanjiri\n"
    "• 📸 Sayt skrinshoti\n\n"
    "━━━ *Secretary Mode* ━━━\n"
    "🤖 Telegram Business orqali botni ulang — shaxsiy chatlaringizni avtomatik himoyalaydi.\n"
    "Yoqish: Settings → Business → Chatbots → Bu bot"
)

TEXTS["ru"]["help_message"] = (
    "📖 *Xavfsizmi? Bot — Все Команды:*\n\n"
    "━━━ *Основные Проверки* ━━━\n"
    "🔗 *Отправить ссылку* — многоуровневый анализ (Trust Score, SSL, typosquatting, редиректы)\n"
    "📱 *Отправить APK* — сканирование через VirusTotal (разрешения, сеть, sandbox)\n"
    "📸 *Фото QR-кода* — извлечение и проверка URL\n\n"
    "━━━ *Команды* ━━━\n"
    "/breach — Проверка утечки email\n"
    "/scammer @username — Проверка аккаунта на мошенничество\n"
    "/privacy https://... — Анализ приватности профиля\n"
    "/phish — Тест друзей на фишинг\n"
    "/tips — Ежедневные советы (on/off)\n"
    "/top — Таблица лидеров рефералов\n"
    "/referral — Пригласить друзей\n"
    "/premium — Купить Premium / Промокод\n"
    "/history — История проверок\n"
    "/report https://... — Сообщить об опасной ссылке\n"
    "/feedback текст — Обратная связь\n"
    "/language — Сменить язык\n\n"
    "━━━ *Автоматический Анализ* ━━━\n"
    "При каждой проверке ссылки автоматически:\n"
    "• 🎯 Trust Score (0-100)\n"
    "• 🔒 Проверка SSL сертификата\n"
    "• 🔤 Обнаружение тайпосквоттинга\n"
    "• 🔀 Раскрытие коротких ссылок\n"
    "• 🔗 Цепочка редиректов\n"
    "• 📸 Скриншот сайта\n\n"
    "━━━ *Режим Секретаря* ━━━\n"
    "🤖 Подключите через Telegram Business — автоматическая защита личных чатов.\n"
    "Включить: Settings → Business → Chatbots → Этот бот"
)

TEXTS["en"]["help_message"] = (
    "📖 *Xavfsizmi? Bot — All Commands:*\n\n"
    "━━━ *Core Scans* ━━━\n"
    "🔗 *Send a link* — multi-layer analysis (Trust Score, SSL, typosquatting, redirects)\n"
    "📱 *Send APK file* — VirusTotal scan (permissions, network, sandbox)\n"
    "📸 *QR code photo* — extract and scan URL inside\n\n"
    "━━━ *Commands* ━━━\n"
    "/breach — Check email data leaks\n"
    "/scammer @username — Check if account is a scammer\n"
    "/privacy https://... — Profile privacy analysis\n"
    "/phish — Test your friends with phishing sim\n"
    "/tips — Daily security tips (on/off)\n"
    "/top — Referral leaderboard\n"
    "/referral — Get your invite link\n"
    "/premium — Buy Premium / Promo code\n"
    "/history — Check history\n"
    "/report https://... — Report dangerous link\n"
    "/feedback text — Send feedback\n"
    "/language — Change language\n\n"
    "━━━ *Auto-Analysis* ━━━\n"
    "Every link check automatically includes:\n"
    "• 🎯 Trust Score (0-100)\n"
    "• 🔒 SSL certificate check\n"
    "• 🔤 Typosquatting detection\n"
    "• 🔀 Short URL expansion\n"
    "• 🔗 Redirect chain tracking\n"
    "• 📸 Website screenshot\n\n"
    "━━━ *Secretary Mode* ━━━\n"
    "🤖 Connect via Telegram Business — auto-protects your personal chats.\n"
    "Enable: Settings → Business → Chatbots → This bot"
)



# ─── ADD TO GROUP BUTTON & PHISH COPY BUTTON ──────────────────────────────────

TEXTS["uz"]["add_to_group_btn"] = "➕ Guruhga qo'shish"
TEXTS["ru"]["add_to_group_btn"] = "➕ Добавить в группу"
TEXTS["en"]["add_to_group_btn"] = "➕ Add to group"

TEXTS["uz"]["phish_copy_btn"] = "📋 Do'stga yuborish"
TEXTS["ru"]["phish_copy_btn"] = "📋 Отправить другу"
TEXTS["en"]["phish_copy_btn"] = "📋 Send to friend"



# ─── HARDCODED MESSAGE FIXES (all translated) ─────────────────────────────────

TEXTS["uz"]["phish_self_click"] = "🎣 Bu sizning shaxsiy fishing testingiz. Uni do'stlaringizga yuboring!"
TEXTS["ru"]["phish_self_click"] = "🎣 Это ваш собственный фишинг-тест. Отправьте его друзьям!"
TEXTS["en"]["phish_self_click"] = "🎣 This is your own phishing test. Send it to your friends!"

TEXTS["uz"]["phish_victim_warning"] = (
    "🚨 *DIQQAT! Siz fishing tuzog'iga tushdingiz!*\n\n"
    "Bu do'stingiz yuborgan *Xavfsizmi? Bot* testi edi.\n"
    "Real hayotda skamer parollaringizni o'g'irlashi mumkin edi!\n\n"
    "🛡 Shubhali linkni doim @XavfsizmiBot orqali tekshiring.\n"
    "💡 Do'stlaringizni sinang: /phish"
)
TEXTS["ru"]["phish_victim_warning"] = (
    "🚨 *ВНИМАНИЕ! Вы попались на фишинг!*\n\n"
    "Это был тест от вашего друга через *Xavfsizmi? Bot*.\n"
    "В реальной жизни мошенник мог бы украсть ваши пароли!\n\n"
    "🛡 Всегда проверяйте подозрительные ссылки через @XavfsizmiBot.\n"
    "💡 Проверьте своих друзей: /phish"
)
TEXTS["en"]["phish_victim_warning"] = (
    "🚨 *WARNING! You fell for a phishing trap!*\n\n"
    "This was a security test from your friend via *Xavfsizmi? Bot*.\n"
    "In real life, a scammer could have stolen your passwords!\n\n"
    "🛡 Always check suspicious links via @XavfsizmiBot.\n"
    "💡 Test your friends: /phish"
)

TEXTS["uz"]["referral_success_notify"] = "🎉 Yangi do'st taklif qildingiz! +1 bepul /breach balansi."
TEXTS["ru"]["referral_success_notify"] = "🎉 Новый друг приглашён! +1 бесплатная проверка /breach."
TEXTS["en"]["referral_success_notify"] = "🎉 New friend invited! +1 free /breach check."

TEXTS["uz"]["phish_intro"] = "🎣 Fishing Simulyatsiya Yaratildi!\n\nPastdagi xabarni do'stingizga forward qiling yoki nusxalang.\nBossa — ogohlantirish oladi, siz xabar olasiz.\n\n🔄 Boshqa shablon: /phish"
TEXTS["ru"]["phish_intro"] = "🎣 Фишинг-симуляция создана!\n\nПерешлите сообщение ниже другу или скопируйте.\nКогда нажмёт — получит предупреждение, а вы уведомление.\n\n🔄 Другой шаблон: /phish"
TEXTS["en"]["phish_intro"] = "🎣 Phishing Simulation Created!\n\nForward the message below to your friend or copy it.\nIf they click — they get a warning, you get notified.\n\n🔄 Another template: /phish"

TEXTS["uz"]["group_admin_only"] = "❗ Faqat guruh adminlari tilni o'zgartira oladi."
TEXTS["ru"]["group_admin_only"] = "❗ Только администраторы группы могут менять язык."
TEXTS["en"]["group_admin_only"] = "❗ Only group admins can change the language."

TEXTS["uz"]["error_send_failed"] = "❌ Xabarni adminlarga yuborib bo'lmadi."
TEXTS["ru"]["error_send_failed"] = "❌ Не удалось отправить сообщение администраторам."
TEXTS["en"]["error_send_failed"] = "❌ Could not send message to admins."



TEXTS["uz"]["breach_cancel"] = "❌ Bekor qilindi."
TEXTS["ru"]["breach_cancel"] = "❌ Отменено."
TEXTS["en"]["breach_cancel"] = "❌ Cancelled."



# ─── URL SCAN REPORT LABELS (all translated) ──────────────────────────────────

TEXTS["uz"]["scan_header"] = "🛡 *SafeLink Chuqur Tahlil:*"
TEXTS["ru"]["scan_header"] = "🛡 *SafeLink Глубокий Анализ:*"
TEXTS["en"]["scan_header"] = "🛡 *SafeLink Deep Analysis:*"

TEXTS["uz"]["trust_score_label"] = "Ishonch Darajasi"
TEXTS["ru"]["trust_score_label"] = "Уровень Доверия"
TEXTS["en"]["trust_score_label"] = "Trust Score"

TEXTS["uz"]["threats"] = "tahdid"
TEXTS["ru"]["threats"] = "угроз"
TEXTS["en"]["threats"] = "threats"

TEXTS["uz"]["dangerous"] = "Xavfli"
TEXTS["ru"]["dangerous"] = "Опасно"
TEXTS["en"]["dangerous"] = "Dangerous"

TEXTS["uz"]["clean"] = "Toza"
TEXTS["ru"]["clean"] = "Чисто"
TEXTS["en"]["clean"] = "Clean"

TEXTS["uz"]["threat_groups"] = "tahdid guruhi"
TEXTS["ru"]["threat_groups"] = "групп угроз"
TEXTS["en"]["threat_groups"] = "threat groups"

TEXTS["uz"]["score"] = "skor"
TEXTS["ru"]["score"] = "оценка"
TEXTS["en"]["score"] = "score"

TEXTS["uz"]["domain_age_label"] = "Domen yoshi"
TEXTS["ru"]["domain_age_label"] = "Возраст домена"
TEXTS["en"]["domain_age_label"] = "Domain age"

TEXTS["uz"]["days"] = "kun"
TEXTS["ru"]["days"] = "дней"
TEXTS["en"]["days"] = "days"

TEXTS["uz"]["new_domain_warning"] = "Juda yangi domen! Fishing bo'lishi mumkin!"
TEXTS["ru"]["new_domain_warning"] = "Очень новый домен! Возможен фишинг!"
TEXTS["en"]["new_domain_warning"] = "Very new domain! Could be phishing!"

TEXTS["uz"]["short_url_expanded"] = "Qisqa havola kengaytirildi"
TEXTS["ru"]["short_url_expanded"] = "Короткая ссылка раскрыта"
TEXTS["en"]["short_url_expanded"] = "Short URL expanded"

TEXTS["uz"]["screenshot_link"] = "Sayt ko'rinishi"
TEXTS["ru"]["screenshot_link"] = "Вид сайта"
TEXTS["en"]["screenshot_link"] = "Website preview"

TEXTS["uz"]["typo_warning"] = "Bu domen `{domain}` ga juda o'xshash! Fishing bo'lishi mumkin!"
TEXTS["ru"]["typo_warning"] = "Этот домен очень похож на `{domain}`! Возможен фишинг!"
TEXTS["en"]["typo_warning"] = "This domain looks very similar to `{domain}`! Could be phishing!"

# ─── LEADERBOARD LABELS (all translated) ──────────────────────────────────────

TEXTS["uz"]["referrals_count"] = "ta taklif"
TEXTS["ru"]["referrals_count"] = "приглашений"
TEXTS["en"]["referrals_count"] = "referrals"

TEXTS["uz"]["your_position"] = "Sizning o'rningiz"
TEXTS["ru"]["your_position"] = "Ваша позиция"
TEXTS["en"]["your_position"] = "Your position"

TEXTS["uz"]["leaderboard_reward"] = "🏆 *Tabriklaymiz!* Siz bu oyning eng faol taklif qiluvchisi bo'ldingiz!\n\n🎁 30 kunlik bepul Premium taqdim etildi.\n📊 Sizning taklif sonatingiz: {count} ta"
TEXTS["ru"]["leaderboard_reward"] = "🏆 *Поздравляем!* Вы стали лучшим рефералом этого месяца!\n\n🎁 Вам предоставлено 30 дней бесплатного Premium.\n📊 Ваши приглашения: {count}"
TEXTS["en"]["leaderboard_reward"] = "🏆 *Congratulations!* You are this month's top referrer!\n\n🎁 You've been awarded 30 days free Premium.\n📊 Your referrals: {count}"



# ─── CONVERSATION PROMPTS (ask for input) ─────────────────────────────────────

TEXTS["uz"]["scammer_ask"] = "👤 *Skammer Tekshiruvi*\n\nTekshirmoqchi bo'lgan username yoki telefon raqamni yuboring:"
TEXTS["ru"]["scammer_ask"] = "👤 *Проверка Скаммера*\n\nОтправьте username или номер телефона для проверки:"
TEXTS["en"]["scammer_ask"] = "👤 *Scammer Check*\n\nSend the username or phone number to check:"

TEXTS["uz"]["privacy_ask"] = "🔏 *Maxfiylik Tahlili*\n\nProfil havolasini yuboring (Instagram, Facebook, va h.k.):"
TEXTS["ru"]["privacy_ask"] = "🔏 *Анализ Приватности*\n\nОтправьте ссылку на профиль (Instagram, Facebook и т.д.):"
TEXTS["en"]["privacy_ask"] = "🔏 *Privacy Analysis*\n\nSend the profile URL (Instagram, Facebook, etc.):"

TEXTS["uz"]["report_ask"] = "🚨 *Xavfli Havola Xabari*\n\nXavfli deb hisoblagan havolani yuboring:"
TEXTS["ru"]["report_ask"] = "🚨 *Сообщить об Опасной Ссылке*\n\nОтправьте ссылку, которую считаете опасной:"
TEXTS["en"]["report_ask"] = "🚨 *Report Dangerous Link*\n\nSend the link you consider dangerous:"

TEXTS["uz"]["feedback_ask"] = "📩 *Taklif / Shikoyat*\n\nXabaringizni yozing (to'g'ridan-to'g'ri adminga yuboriladi):"
TEXTS["ru"]["feedback_ask"] = "📩 *Предложение / Жалоба*\n\nНапишите сообщение (отправится напрямую администратору):"
TEXTS["en"]["feedback_ask"] = "📩 *Feedback / Complaint*\n\nWrite your message (it will be sent directly to the admin):"

TEXTS["uz"]["scammer_result_title"] = "Skammer Tekshiruvi"
TEXTS["ru"]["scammer_result_title"] = "Проверка Скаммера"
TEXTS["en"]["scammer_result_title"] = "Scammer Check"

TEXTS["uz"]["warning_found"] = "OGOHLANTIRISH topildi"
TEXTS["ru"]["warning_found"] = "ПРЕДУПРЕЖДЕНИЕ найдено"
TEXTS["en"]["warning_found"] = "WARNING found"

TEXTS["uz"]["sources_checked"] = "Tekshirilgan bazalar"
TEXTS["ru"]["sources_checked"] = "Проверенные базы"
TEXTS["en"]["sources_checked"] = "Sources checked"

TEXTS["uz"]["no_warnings"] = "Hech qanday ogohlantirish topilmadi."
TEXTS["ru"]["no_warnings"] = "Предупреждений не найдено."
TEXTS["en"]["no_warnings"] = "No warnings found."

TEXTS["uz"]["no_guarantee"] = "100% kafolat bermaydi. Ehtiyot bo'ling!"
TEXTS["ru"]["no_guarantee"] = "100% гарантии нет. Будьте осторожны!"
TEXTS["en"]["no_guarantee"] = "No 100% guarantee. Stay careful!"

TEXTS["uz"]["privacy_result_title"] = "Maxfiylik Tahlili"
TEXTS["ru"]["privacy_result_title"] = "Анализ Приватности"
TEXTS["en"]["privacy_result_title"] = "Privacy Analysis"

TEXTS["uz"]["privacy_score"] = "Maxfiylik Bali"
TEXTS["ru"]["privacy_score"] = "Оценка Приватности"
TEXTS["en"]["privacy_score"] = "Privacy Score"

TEXTS["uz"]["findings"] = "Topilmalar"
TEXTS["ru"]["findings"] = "Находки"
TEXTS["en"]["findings"] = "Findings"

TEXTS["uz"]["recommendations"] = "Tavsiyalar"
TEXTS["ru"]["recommendations"] = "Рекомендации"
TEXTS["en"]["recommendations"] = "Recommendations"

TEXTS["uz"]["privacy_error"] = "Profilni tekshirib bo'lmadi"
TEXTS["ru"]["privacy_error"] = "Не удалось проверить профиль"
TEXTS["en"]["privacy_error"] = "Could not check profile"

TEXTS["uz"]["report_admin_alert"] = "Xavfli havola xabari"
TEXTS["ru"]["report_admin_alert"] = "Жалоба на ссылку"
TEXTS["en"]["report_admin_alert"] = "Dangerous link report"

TEXTS["uz"]["feedback_admin_title"] = "Yangi taklif/shikoyat"
TEXTS["ru"]["feedback_admin_title"] = "Новое предложение/жалоба"
TEXTS["en"]["feedback_admin_title"] = "New feedback/complaint"



# ─── PREMIUM PRICING TEXTS (updated) ─────────────────────────────────────────

TEXTS["uz"]["month"] = "oy"
TEXTS["ru"]["month"] = "мес"
TEXTS["en"]["month"] = "mo"

TEXTS["uz"]["months"] = "oy"
TEXTS["ru"]["months"] = "мес"
TEXTS["en"]["months"] = "mo"

TEXTS["uz"]["premium_already_active_with_expiry"] = "⭐ Sizda Premium faol!\n📅 Muddati: `{expiry}` gacha"
TEXTS["ru"]["premium_already_active_with_expiry"] = "⭐ У вас активен Premium!\n📅 Действует до: `{expiry}`"
TEXTS["en"]["premium_already_active_with_expiry"] = "⭐ You have active Premium!\n📅 Expires: `{expiry}`"

TEXTS["uz"]["premium_success_with_days"] = "🎉 *To'lov muvaffaqiyatli!* Sizga {days} kunlik Premium taqdim etildi."
TEXTS["ru"]["premium_success_with_days"] = "🎉 *Оплата успешна!* Вам предоставлено {days} дней Premium."
TEXTS["en"]["premium_success_with_days"] = "🎉 *Payment successful!* You've been granted {days} days of Premium."

TEXTS["uz"]["premium_info"] = (
    "⚡ *Xavfsizmi? Premium*\n\n"
    "✅ Cheksiz tekshiruv (URL + APK + QR)\n"
    "✅ /breach email tekshiruvi\n"
    "✅ Reklamasiz va yuqori tezlik\n\n"
    "💰 *Narxlar:*\n"
    "• 1 oy: 25 Stars yoki 9,990 so'm\n"
    "• 3 oy: 65 Stars yoki 24,990 so'm (17% tejash!) 🔥\n\n"
    "👇 *Rejani tanlang:*"
)
TEXTS["ru"]["premium_info"] = (
    "⚡ *Xavfsizmi? Premium*\n\n"
    "✅ Безлимитные проверки (URL + APK + QR)\n"
    "✅ Проверка утечек /breach\n"
    "✅ Без рекламы и высокая скорость\n\n"
    "💰 *Цены:*\n"
    "• 1 мес: 25 Stars или 9,990 сум\n"
    "• 3 мес: 65 Stars или 24,990 сум (скидка 17%!) 🔥\n\n"
    "👇 *Выберите план:*"
)
TEXTS["en"]["premium_info"] = (
    "⚡ *Xavfsizmi? Premium*\n\n"
    "✅ Unlimited checks (URL + APK + QR)\n"
    "✅ Email breach /breach access\n"
    "✅ No ads and high speed\n\n"
    "💰 *Pricing:*\n"
    "• 1 month: 25 Stars or 9,990 UZS\n"
    "• 3 months: 65 Stars or 24,990 UZS (save 17%!) 🔥\n\n"
    "👇 *Choose a plan:*"
)



# ─── GROUP PREMIUM TEXTS ──────────────────────────────────────────────────────

TEXTS["uz"]["group_premium_active"] = "⭐ Bu guruhda Premium faol!\n📅 Muddati: `{expiry}` gacha\n♾ Cheksiz tekshiruvlar"
TEXTS["ru"]["group_premium_active"] = "⭐ В этой группе активен Premium!\n📅 До: `{expiry}`\n♾ Безлимитные проверки"
TEXTS["en"]["group_premium_active"] = "⭐ This group has active Premium!\n📅 Until: `{expiry}`\n♾ Unlimited checks"

TEXTS["uz"]["group_premium_info"] = (
    "⚡ *Guruh Premium*\n\n"
    "✅ Cheksiz tekshiruv (kunlik limit yo'q)\n"
    "✅ Tezkor skanerlash\n\n"
    "💰 *Narxlar:*\n"
    "• 1 oy: 50 Stars yoki 19,990 so'm\n"
    "• 3 oy: 130 Stars yoki 49,990 so'm 🔥\n\n"
    "👇 *Rejani tanlang:*"
)
TEXTS["ru"]["group_premium_info"] = (
    "⚡ *Премиум для Группы*\n\n"
    "✅ Безлимитные проверки (без дневного лимита)\n"
    "✅ Быстрое сканирование\n\n"
    "💰 *Цены:*\n"
    "• 1 мес: 50 Stars или 19,990 сум\n"
    "• 3 мес: 130 Stars или 49,990 сум 🔥\n\n"
    "👇 *Выберите план:*"
)
TEXTS["en"]["group_premium_info"] = (
    "⚡ *Group Premium*\n\n"
    "✅ Unlimited checks (no daily limit)\n"
    "✅ Fast scanning\n\n"
    "💰 *Pricing:*\n"
    "• 1 month: 50 Stars or 19,990 UZS\n"
    "• 3 months: 130 Stars or 49,990 UZS 🔥\n\n"
    "👇 *Choose a plan:*"
)

TEXTS["uz"]["group_premium_success"] = "🎉 *Guruh Premium faollashtirildi!* {days} kunlik cheksiz himoya."
TEXTS["ru"]["group_premium_success"] = "🎉 *Премиум группы активирован!* {days} дней безлимитной защиты."
TEXTS["en"]["group_premium_success"] = "🎉 *Group Premium activated!* {days} days of unlimited protection."



TEXTS["uz"]["group_premium_admin_only"] = "❗ Guruh Premium faqat guruh adminlari tomonidan xarid qilinishi mumkin."
TEXTS["ru"]["group_premium_admin_only"] = "❗ Премиум для группы могут купить только администраторы группы."
TEXTS["en"]["group_premium_admin_only"] = "❗ Group Premium can only be purchased by group admins."



# ─── PAYNET QR PAYMENT TEXTS ──────────────────────────────────────────────────

TEXTS["uz"]["pay_via_qr"] = "QR orqali to'lash"
TEXTS["ru"]["pay_via_qr"] = "Оплата по QR"
TEXTS["en"]["pay_via_qr"] = "Pay via QR"

# Override premium_info to show new payment methods
TEXTS["uz"]["premium_info"] = (
    "⚡ *Xavfsizmi? Premium*\n\n"
    "✅ Cheksiz tekshiruv (URL + APK + QR)\n"
    "✅ /breach email tekshiruvi\n"
    "✅ Reklamasiz va yuqori tezlik\n\n"
    "💰 *Narxlar:*\n"
    "• 1 oy: 25 Stars yoki 9,990 so'm (Paynet QR)\n"
    "• 3 oy: 65 Stars yoki 24,990 so'm (Paynet QR) 🔥\n\n"
    "⭐ Stars — Telegram ichida to'lov\n"
    "💳 Paynet — QR skanerlash orqali\n\n"
    "👇 *Tanlang:*"
)
TEXTS["ru"]["premium_info"] = (
    "⚡ *Xavfsizmi? Premium*\n\n"
    "✅ Безлимитные проверки (URL + APK + QR)\n"
    "✅ Проверка утечек /breach\n"
    "✅ Без рекламы и высокая скорость\n\n"
    "💰 *Цены:*\n"
    "• 1 мес: 25 Stars или 9,990 сум (Paynet QR)\n"
    "• 3 мес: 65 Stars или 24,990 сум (Paynet QR) 🔥\n\n"
    "⭐ Stars — оплата внутри Telegram\n"
    "💳 Paynet — сканируйте QR-код\n\n"
    "👇 *Выберите:*"
)
TEXTS["en"]["premium_info"] = (
    "⚡ *Xavfsizmi? Premium*\n\n"
    "✅ Unlimited checks (URL + APK + QR)\n"
    "✅ Email breach /breach access\n"
    "✅ No ads and high speed\n\n"
    "💰 *Pricing:*\n"
    "• 1 month: 25 Stars or 9,990 UZS (Paynet QR)\n"
    "• 3 months: 65 Stars or 24,990 UZS (Paynet QR) 🔥\n\n"
    "⭐ Stars — pay inside Telegram\n"
    "💳 Paynet — scan QR code to pay\n\n"
    "👇 *Choose:*"
)



# ─── PAYNET PAYMENT FLOW TEXTS ────────────────────────────────────────────────

TEXTS["uz"]["open_paynet"] = "Paynet QR ni ochish"
TEXTS["ru"]["open_paynet"] = "Открыть Paynet QR"
TEXTS["en"]["open_paynet"] = "Open Paynet QR"

TEXTS["uz"]["paynet_instructions"] = (
    "💳 *Paynet orqali to'lov*\n\n"
    "📋 *Reja:* {duration} — {price}\n\n"
    "📌 *Qadamlar:*\n"
    "1️⃣ Pastdagi tugmani bosing va QR kodni skanerlang\n"
    "2️⃣ *Aynan* `{price}` so'm to'lang\n"
    "3️⃣ To'lovdan so'ng /receipt buyrug'ini bosing\n"
    "4️⃣ Kvitansiya raqamini yuboring\n\n"
    "⚡ *Tavsiya:* Telegram Stars orqali to'lov tezroq va avtomatik!\n\n"
    "⚠️ *MUHIM OGOHLANTIRISHLAR:*\n"
    "• Noto'g'ri summa to'langan hollarda pul QAYTARILMAYDI\n"
    "• Kam summa to'lasangiz Premium BERILMAYDI\n"
    "• Faqat ko'rsatilgan summani to'lang: `{price}` so'm\n"
    "• Kvitansiya raqamisiz murojaat qabul qilinmaydi"
)
TEXTS["ru"]["paynet_instructions"] = (
    "💳 *Оплата через Paynet*\n\n"
    "📋 *План:* {duration} — {price}\n\n"
    "📌 *Шаги:*\n"
    "1️⃣ Нажмите кнопку ниже и отсканируйте QR-код\n"
    "2️⃣ Оплатите *ровно* `{price}` сум\n"
    "3️⃣ После оплаты нажмите /receipt\n"
    "4️⃣ Отправьте номер квитанции\n\n"
    "⚡ *Рекомендация:* Telegram Stars — быстрее и автоматически!\n\n"
    "⚠️ *ВАЖНЫЕ ПРЕДУПРЕЖДЕНИЯ:*\n"
    "• При неправильной сумме деньги НЕ ВОЗВРАЩАЮТСЯ\n"
    "• При недоплате Premium НЕ АКТИВИРУЕТСЯ\n"
    "• Оплатите ровно указанную сумму: `{price}` сум\n"
    "• Без номера квитанции обращения не принимаются"
)
TEXTS["en"]["paynet_instructions"] = (
    "💳 *Payment via Paynet*\n\n"
    "📋 *Plan:* {duration} — {price}\n\n"
    "📌 *Steps:*\n"
    "1️⃣ Tap the button below and scan the QR code\n"
    "2️⃣ Pay *exactly* `{price}` UZS\n"
    "3️⃣ After payment, tap /receipt\n"
    "4️⃣ Send the receipt/transaction number\n\n"
    "⚡ *Tip:* Telegram Stars is faster and automatic!\n\n"
    "⚠️ *IMPORTANT DISCLAIMERS:*\n"
    "• Wrong amounts are NON-REFUNDABLE\n"
    "• Underpayment will NOT activate Premium\n"
    "• Pay exactly the stated amount: `{price}` UZS\n"
    "• No receipt number = no support"
)

TEXTS["uz"]["paynet_send_receipt"] = "🧾 *Kvitansiya Yuborish*\n\nPaynet to'lov kvitansiya raqamini yuboring yoki skrinshot yuboring:"
TEXTS["ru"]["paynet_send_receipt"] = "🧾 *Отправить Квитанцию*\n\nОтправьте номер квитанции Paynet или скриншот:"
TEXTS["en"]["paynet_send_receipt"] = "🧾 *Send Receipt*\n\nSend your Paynet receipt/transaction number or screenshot:"

TEXTS["uz"]["paynet_receipt_sent"] = "✅ Kvitansiya adminga yuborildi! Tekshirilgandan so'ng Premium faollashtiriladi.\n\n⏳ Odatda 1-24 soat ichida tasdiqlanadi."
TEXTS["ru"]["paynet_receipt_sent"] = "✅ Квитанция отправлена админу! После проверки Premium будет активирован.\n\n⏳ Обычно подтверждение занимает 1-24 часа."
TEXTS["en"]["paynet_receipt_sent"] = "✅ Receipt sent to admin! Premium will be activated after verification.\n\n⏳ Usually confirmed within 1-24 hours."

TEXTS["uz"]["paynet_rejected"] = "❌ *To'lov rad etildi.*\n\nSizning Paynet to'lovingiz tasdiqlanmadi. Sabablari:\n• Noto'g'ri summa to'langan\n• Kvitansiya raqami noto'g'ri\n\nQayta urinib ko'ring yoki ⭐ Stars orqali to'lang."
TEXTS["ru"]["paynet_rejected"] = "❌ *Платёж отклонён.*\n\nВаш платёж через Paynet не подтверждён. Причины:\n• Неверная сумма\n• Неверный номер квитанции\n\nПопробуйте снова или оплатите ⭐ Stars."
TEXTS["en"]["paynet_rejected"] = "❌ *Payment rejected.*\n\nYour Paynet payment was not confirmed. Reasons:\n• Wrong amount paid\n• Invalid receipt number\n\nTry again or pay via ⭐ Stars."



# ─── SECRETARY MODE TEXTS ─────────────────────────────────────────────────────

TEXTS["uz"]["secretary_enabled"] = (
    "🤖 *Secretary Mode faollashtirildi!*\n\n"
    "Endi shaxsiy chatlaringizga kelgan xabarlarni avtomatik tekshiraman:\n"
    "• 🔗 Havolalar — fishing/virus\n"
    "• 📱 APK fayllar — zararli kod\n"
    "• 📸 QR kodlar — ichidagi URL\n"
    "• 📝 Matn — skam belgilari\n\n"
    "✅ Xavfsiz → jim turaman\n"
    "🚨 Xavfli → darhol ogohlantiraman\n"
    "📱 APK → doim natija ko'rsataman\n\n"
    "❌ O'chirish: Settings → Business → Chatbots → Olib tashlash"
)
TEXTS["ru"]["secretary_enabled"] = (
    "🤖 *Режим Секретаря активирован!*\n\n"
    "Теперь я автоматически проверяю сообщения в ваших личных чатах:\n"
    "• 🔗 Ссылки — фишинг/вирусы\n"
    "• 📱 APK файлы — вредоносный код\n"
    "• 📸 QR-коды — URL внутри\n"
    "• 📝 Текст — признаки мошенничества\n\n"
    "✅ Безопасно → молчу\n"
    "🚨 Опасно → сразу предупрежу\n"
    "📱 APK → всегда показываю результат\n\n"
    "❌ Отключить: Settings → Business → Chatbots → Удалить"
)
TEXTS["en"]["secretary_enabled"] = (
    "🤖 *Secretary Mode activated!*\n\n"
    "I will now auto-scan messages in your personal chats:\n"
    "• 🔗 Links — phishing/malware\n"
    "• 📱 APK files — malicious code\n"
    "• 📸 QR codes — URL inside\n"
    "• 📝 Text — scam patterns\n\n"
    "✅ Safe → I stay silent\n"
    "🚨 Dangerous → I alert immediately\n"
    "📱 APK → I always show results\n\n"
    "❌ Disable: Settings → Business → Chatbots → Remove"
)

TEXTS["uz"]["secretary_disabled"] = "🤖 Secretary Mode o'chirildi. Endi xabarlaringizni tekshirmayman."
TEXTS["ru"]["secretary_disabled"] = "🤖 Режим Секретаря отключён. Больше не проверяю сообщения."
TEXTS["en"]["secretary_disabled"] = "🤖 Secretary Mode disabled. No longer scanning your messages."



# ─── BREACH + PASSWORD CHECK TEXTS ────────────────────────────────────────────

TEXTS["uz"]["breach_ask_input"] = (
    "🔐 *Email & Parol Tekshiruvi*\n\n"
    "📧 Email yuboring — ma'lumotlar sizib chiqqanini tekshiraman\n"
    "🔑 Yoki parol yuboring — leak bazalarida borligini tekshiraman\n\n"
    "⚠️ Parolingiz xavfsiz — faqat SHA1 hashning 5 belgisi yuboriladi\n\n"
    "👇 Email yoki parolni yuboring:"
)
TEXTS["ru"]["breach_ask_input"] = (
    "🔐 *Проверка Email & Пароля*\n\n"
    "📧 Отправьте email — проверю утечки данных\n"
    "🔑 Или отправьте пароль — проверю в базах утечек\n\n"
    "⚠️ Ваш пароль в безопасности — отправляются только 5 символов SHA1 хеша\n\n"
    "👇 Отправьте email или пароль:"
)
TEXTS["en"]["breach_ask_input"] = (
    "🔐 *Email & Password Check*\n\n"
    "📧 Send an email — I'll check for data breaches\n"
    "🔑 Or send a password — I'll check if it's been leaked\n\n"
    "⚠️ Your password is safe — only 5 chars of SHA1 hash are sent\n\n"
    "👇 Send email or password:"
)

TEXTS["uz"]["breach_credits_left"] = "Sizda {credits} ta bepul tekshiruv bor."
TEXTS["ru"]["breach_credits_left"] = "У вас {credits} бесплатных проверок."
TEXTS["en"]["breach_credits_left"] = "You have {credits} free checks left."

TEXTS["uz"]["password_compromised"] = "🚨 *PAROL XAVF OSTIDA!*\n\n🔑 Bu parol ma'lumotlar sizib chiqishlarida *{count}* marta topilgan!\n\n⚠️ Bu parolni ISHLATMANG!\n💡 Yangi, kuchli parol yarating (12+ belgi, aralash harflar + raqamlar)"
TEXTS["ru"]["password_compromised"] = "🚨 *ПАРОЛЬ СКОМПРОМЕТИРОВАН!*\n\n🔑 Этот пароль найден в утечках данных *{count}* раз!\n\n⚠️ НЕ используйте этот пароль!\n💡 Создайте новый сильный пароль (12+ символов, буквы + цифры)"
TEXTS["en"]["password_compromised"] = "🚨 *PASSWORD COMPROMISED!*\n\n🔑 This password has been found in data breaches *{count}* times!\n\n⚠️ DO NOT use this password!\n💡 Create a new strong password (12+ chars, mixed letters + numbers)"

TEXTS["uz"]["password_safe"] = "✅ *PAROL XAVFSIZ*\n\n🔑 Bu parol ma'lum sizib chiqishlarda topilmadi.\n\n💡 Baribir, uni vaqti-vaqti bilan yangilab turing!"
TEXTS["ru"]["password_safe"] = "✅ *ПАРОЛЬ В БЕЗОПАСНОСТИ*\n\n🔑 Этот пароль не найден в известных утечках.\n\n💡 Всё равно рекомендуем периодически его менять!"
TEXTS["en"]["password_safe"] = "✅ *PASSWORD SAFE*\n\n🔑 This password was not found in known data breaches.\n\n💡 Still, update it periodically!"

TEXTS["uz"]["password_check_error"] = "⚠️ Parol tekshirish xizmati hozir ishlamayapti. Keyinroq urinib ko'ring."
TEXTS["ru"]["password_check_error"] = "⚠️ Сервис проверки паролей сейчас недоступен. Попробуйте позже."
TEXTS["en"]["password_check_error"] = "⚠️ Password check service is currently unavailable. Try again later."

TEXTS["uz"]["more_breaches"] = "ta yana"
TEXTS["ru"]["more_breaches"] = "ещё"
TEXTS["en"]["more_breaches"] = "more"



# ─── AI FEATURES (ask / analyze / verdict) ────────────────────────────────────

TEXTS["uz"]["ai_thinking"] = "🤖 O'ylayapman..."
TEXTS["ru"]["ai_thinking"] = "🤖 Думаю..."
TEXTS["en"]["ai_thinking"] = "🤖 Thinking..."

TEXTS["uz"]["ai_unavailable"] = "⚠️ AI yordamchi hozir ishlamayapti. Keyinroq urinib ko'ring."
TEXTS["ru"]["ai_unavailable"] = "⚠️ AI-помощник сейчас недоступен. Попробуйте позже."
TEXTS["en"]["ai_unavailable"] = "⚠️ AI assistant is currently unavailable. Try again later."

TEXTS["uz"]["ask_prompt"] = "🤖 *AI Xavfsizlik Yordamchisi*\n\nKiberxavfsizlik bo'yicha savolingizni yozing (parollar, fishing, viruslar, maxfiylik va h.k.):"
TEXTS["ru"]["ask_prompt"] = "🤖 *AI Помощник по Безопасности*\n\nНапишите ваш вопрос по кибербезопасности (пароли, фишинг, вирусы, приватность и т.д.):"
TEXTS["en"]["ask_prompt"] = "🤖 *AI Security Assistant*\n\nWrite your cybersecurity question (passwords, phishing, viruses, privacy, etc.):"

TEXTS["uz"]["analyze_prompt"] = "🔍 *Shubhali Xabar Tahlili*\n\nSizga kelgan shubhali xabarni (SMS, email, Telegram) shu yerga nusxalab yuboring. AI uni firibgarlikka tekshiradi:"
TEXTS["ru"]["analyze_prompt"] = "🔍 *Анализ Подозрительного Сообщения*\n\nСкопируйте сюда подозрительное сообщение (SMS, email, Telegram). AI проверит его на мошенничество:"
TEXTS["en"]["analyze_prompt"] = "🔍 *Suspicious Message Analysis*\n\nPaste the suspicious message you received (SMS, email, Telegram) here. AI will check it for scams:"

TEXTS["uz"]["analyze_result_title"] = "AI Tahlil Natijasi"
TEXTS["ru"]["analyze_result_title"] = "Результат AI Анализа"
TEXTS["en"]["analyze_result_title"] = "AI Analysis Result"

TEXTS["uz"]["ai_verdict_label"] = "AI Xulosasi"
TEXTS["ru"]["ai_verdict_label"] = "Вердикт AI"
TEXTS["en"]["ai_verdict_label"] = "AI Verdict"

# ─── FILE SCANNER ─────────────────────────────────────────────────────────────

TEXTS["uz"]["file_type_unsupported"] = "❌ Bu fayl turi qo'llab-quvvatlanmaydi.\n\n✅ Mumkin: APK, EXE, PDF, DOC(X), XLS(X), ZIP, RAR, JS, JAR va boshqalar."
TEXTS["ru"]["file_type_unsupported"] = "❌ Этот тип файла не поддерживается.\n\n✅ Доступно: APK, EXE, PDF, DOC(X), XLS(X), ZIP, RAR, JS, JAR и др."
TEXTS["en"]["file_type_unsupported"] = "❌ This file type is not supported.\n\n✅ Allowed: APK, EXE, PDF, DOC(X), XLS(X), ZIP, RAR, JS, JAR and more."

TEXTS["uz"]["file_scanning"] = "🔍 *{type}* tahlil qilinmoqda, kuting..."
TEXTS["ru"]["file_scanning"] = "🔍 *{type}* проверяется, подождите..."
TEXTS["en"]["file_scanning"] = "🔍 Scanning *{type}*, please wait..."

TEXTS["uz"]["file_report_title"] = "Fayl Tahlil Hisoboti"
TEXTS["ru"]["file_report_title"] = "Отчёт по Файлу"
TEXTS["en"]["file_report_title"] = "File Scan Report"

TEXTS["uz"]["file_name_label"] = "Fayl"
TEXTS["ru"]["file_name_label"] = "Файл"
TEXTS["en"]["file_name_label"] = "File"

TEXTS["uz"]["file_type_label"] = "Tur"
TEXTS["ru"]["file_type_label"] = "Тип"
TEXTS["en"]["file_type_label"] = "Type"

TEXTS["uz"]["status_label"] = "Holat"
TEXTS["ru"]["status_label"] = "Статус"
TEXTS["en"]["status_label"] = "Status"

TEXTS["uz"]["status_malicious"] = "ZARARLI (Virus)"
TEXTS["ru"]["status_malicious"] = "ВРЕДОНОСНЫЙ (Вирус)"
TEXTS["en"]["status_malicious"] = "MALICIOUS (Virus)"

TEXTS["uz"]["status_suspicious"] = "SHUBHALI"
TEXTS["ru"]["status_suspicious"] = "ПОДОЗРИТЕЛЬНЫЙ"
TEXTS["en"]["status_suspicious"] = "SUSPICIOUS"

TEXTS["uz"]["status_safe"] = "XAVFSIZ"
TEXTS["ru"]["status_safe"] = "БЕЗОПАСНЫЙ"
TEXTS["en"]["status_safe"] = "SAFE"

TEXTS["uz"]["engines_word"] = "ta dvigatel tekshirdi"
TEXTS["ru"]["engines_word"] = "антивирусов проверили"
TEXTS["en"]["engines_word"] = "engines checked"

TEXTS["uz"]["permissions_label"] = "Ruxsatlar"
TEXTS["ru"]["permissions_label"] = "Разрешения"
TEXTS["en"]["permissions_label"] = "Permissions"

TEXTS["uz"]["network_calls_label"] = "Tarmoq so'rovlari"
TEXTS["ru"]["network_calls_label"] = "Сетевые запросы"
TEXTS["en"]["network_calls_label"] = "Network calls"

TEXTS["uz"]["file_timeout"] = "⏳ VirusTotal javob bermadi. Keyinroq urinib ko'ring."
TEXTS["ru"]["file_timeout"] = "⏳ VirusTotal не ответил. Попробуйте позже."
TEXTS["en"]["file_timeout"] = "⏳ VirusTotal timed out. Try again later."

TEXTS["uz"]["file_scan_error"] = "❌ Faylni tekshirishda xatolik yuz berdi."
TEXTS["ru"]["file_scan_error"] = "❌ Ошибка при проверке файла."
TEXTS["en"]["file_scan_error"] = "❌ An error occurred while scanning the file."

# ─── BREACH MONITOR (premium) ─────────────────────────────────────────────────

TEXTS["uz"]["monitor_premium_required"] = (
    "📡 *Email Monitoring — Premium imkoniyat*\n\n"
    "Bir nechta emailingizni qo'shing — bot ularni muntazam tekshiradi va "
    "YANGI ma'lumot sizishi aniqlansa, sizni darhol ogohlantiradi.\n\n"
    "⭐ Bu funksiya faqat Premium foydalanuvchilar uchun."
)
TEXTS["ru"]["monitor_premium_required"] = (
    "📡 *Мониторинг Email — Премиум функция*\n\n"
    "Добавьте несколько email — бот будет регулярно их проверять и "
    "сразу предупредит, если обнаружится НОВАЯ утечка.\n\n"
    "⭐ Эта функция только для Премиум пользователей."
)
TEXTS["en"]["monitor_premium_required"] = (
    "📡 *Email Monitoring — Premium feature*\n\n"
    "Add multiple emails — the bot regularly re-checks them and alerts you "
    "immediately if a NEW breach is detected.\n\n"
    "⭐ This feature is for Premium users only."
)

TEXTS["uz"]["monitor_empty"] = "📡 *Email Monitoring*\n\nHozircha kuzatilayotgan email yo'q.\n\nQo'shish uchun emailni yuboring yoki `/monitor add email@example.com`"
TEXTS["ru"]["monitor_empty"] = "📡 *Мониторинг Email*\n\nПока нет отслеживаемых email.\n\nЧтобы добавить, отправьте email или `/monitor add email@example.com`"
TEXTS["en"]["monitor_empty"] = "📡 *Email Monitoring*\n\nNo monitored emails yet.\n\nTo add one, send an email or `/monitor add email@example.com`"

TEXTS["uz"]["monitor_list_title"] = "📡 *Kuzatilayotgan Emaillar:*"
TEXTS["ru"]["monitor_list_title"] = "📡 *Отслеживаемые Email:*"
TEXTS["en"]["monitor_list_title"] = "📡 *Monitored Emails:*"

TEXTS["uz"]["breaches_word"] = "ta sizish"
TEXTS["ru"]["breaches_word"] = "утечек"
TEXTS["en"]["breaches_word"] = "breaches"

TEXTS["uz"]["monitor_add_hint"] = "➕ Yana qo'shish uchun emailni yuboring."
TEXTS["ru"]["monitor_add_hint"] = "➕ Отправьте email, чтобы добавить ещё."
TEXTS["en"]["monitor_add_hint"] = "➕ Send an email to add another."

TEXTS["uz"]["monitor_invalid_email"] = "❌ Noto'g'ri email format. Masalan: `user@gmail.com`"
TEXTS["ru"]["monitor_invalid_email"] = "❌ Неверный формат email. Например: `user@gmail.com`"
TEXTS["en"]["monitor_invalid_email"] = "❌ Invalid email format. Example: `user@gmail.com`"

TEXTS["uz"]["monitor_limit"] = "❌ Maksimal {limit} ta email kuzatish mumkin."
TEXTS["ru"]["monitor_limit"] = "❌ Можно отслеживать максимум {limit} email."
TEXTS["en"]["monitor_limit"] = "❌ You can monitor up to {limit} emails."

TEXTS["uz"]["monitor_already_added"] = "ℹ️ Bu email allaqachon kuzatilmoqda."
TEXTS["ru"]["monitor_already_added"] = "ℹ️ Этот email уже отслеживается."
TEXTS["en"]["monitor_already_added"] = "ℹ️ This email is already being monitored."

TEXTS["uz"]["monitor_added_safe"] = "✅ `{email}` qo'shildi va kuzatilmoqda.\n\nHozircha hech qanday sizish topilmadi. Yangi sizish aniqlansa, sizni ogohlantiraman."
TEXTS["ru"]["monitor_added_safe"] = "✅ `{email}` добавлен и отслеживается.\n\nПока утечек не найдено. Я предупрежу вас при новой утечке."
TEXTS["en"]["monitor_added_safe"] = "✅ `{email}` added and monitored.\n\nNo breaches found yet. I'll alert you if a new one appears."

TEXTS["uz"]["monitor_added_breached"] = "⚠️ `{email}` qo'shildi.\n\n🔴 Diqqat: bu email allaqachon *{count}* ta sizishda topilgan! Parollaringizni yangilang."
TEXTS["ru"]["monitor_added_breached"] = "⚠️ `{email}` добавлен.\n\n🔴 Внимание: этот email уже найден в *{count}* утечках! Смените пароли."
TEXTS["en"]["monitor_added_breached"] = "⚠️ `{email}` added.\n\n🔴 Warning: this email is already in *{count}* breaches! Update your passwords."

TEXTS["uz"]["monitor_removed"] = "🗑 `{email}` kuzatuvdan olib tashlandi."
TEXTS["ru"]["monitor_removed"] = "🗑 `{email}` удалён из мониторинга."
TEXTS["en"]["monitor_removed"] = "🗑 `{email}` removed from monitoring."

TEXTS["uz"]["monitor_new_breach_alert"] = (
    "🚨 *YANGI SIZISH ANIQLANDI!*\n\n"
    "📧 `{email}` yangi ma'lumotlar sizishida topildi!\n"
    "🔴 Yangi: +{new} | Jami: {total} ta sizish\n\n"
    "⚠️ Zudlik bilan ushbu email bilan bog'liq parollarni o'zgartiring!"
)
TEXTS["ru"]["monitor_new_breach_alert"] = (
    "🚨 *ОБНАРУЖЕНА НОВАЯ УТЕЧКА!*\n\n"
    "📧 `{email}` найден в новой утечке данных!\n"
    "🔴 Новых: +{new} | Всего: {total} утечек\n\n"
    "⚠️ Срочно смените пароли, связанные с этим email!"
)
TEXTS["en"]["monitor_new_breach_alert"] = (
    "🚨 *NEW BREACH DETECTED!*\n\n"
    "📧 `{email}` was found in a new data breach!\n"
    "🔴 New: +{new} | Total: {total} breaches\n\n"
    "⚠️ Change passwords linked to this email immediately!"
)

# ─── WEEKLY REPORT ────────────────────────────────────────────────────────────

TEXTS["uz"]["weekly_report"] = (
    "📊 *Haftalik Hisobotingiz*\n\n"
    "Bu hafta siz:\n"
    "🔍 Jami tekshiruvlar: *{total}*\n"
    "🟢 Xavfsiz: *{safe}*\n"
    "🔴 Xavfli aniqlandi: *{dangerous}*\n\n"
    "🛡 Xavfsizligingiz uchun rahmat! Hushyor bo'ling."
)
TEXTS["ru"]["weekly_report"] = (
    "📊 *Ваш Недельный Отчёт*\n\n"
    "На этой неделе вы:\n"
    "🔍 Всего проверок: *{total}*\n"
    "🟢 Безопасных: *{safe}*\n"
    "🔴 Обнаружено опасных: *{dangerous}*\n\n"
    "🛡 Спасибо за заботу о безопасности! Будьте бдительны."
)
TEXTS["en"]["weekly_report"] = (
    "📊 *Your Weekly Report*\n\n"
    "This week you:\n"
    "🔍 Total checks: *{total}*\n"
    "🟢 Safe: *{safe}*\n"
    "🔴 Dangerous found: *{dangerous}*\n\n"
    "🛡 Thanks for staying safe! Stay vigilant."
)



# ─── UPDATED HELP MESSAGE (with all new features) ─────────────────────────────

TEXTS["uz"]["help_message"] = (
    "📖 *Xavfsizmi? Bot — Barcha Buyruqlar:*\n\n"
    "━━━ *Asosiy Tekshiruvlar* ━━━\n"
    "🔗 *Havola yuborish* — chuqur tahlil + Trust Score + AI xulosa\n"
    "📄 *Fayl yuborish* — APK, PDF, DOC, ZIP, EXE va boshqalarni skanerlash\n"
    "📸 *QR kod rasmi* — ichidagi URL ni topib tekshirish\n\n"
    "━━━ *AI Buyruqlar* ━━━\n"
    "/ask — Kiberxavfsizlik bo'yicha savolingizga AI javob beradi\n"
    "/analyze — Shubhali xabar/SMS ni AI ga tahlil qildirish\n\n"
    "━━━ *Tekshiruv Buyruqlar* ━━━\n"
    "/breach — Email yoki parol sizib chiqqanini tekshirish\n"
    "/monitor — Emaillarni doimiy kuzatish, yangi sizishda ogohlantirish (Premium)\n"
    "/scammer @username — Foydalanuvchi skammer emasligini tekshirish\n\n"
    "━━━ *Boshqa Buyruqlar* ━━━\n"
    "/phish — Do'stlaringizni fishing testi bilan sinash\n"
    "/tips — Kunlik xavfsizlik maslahatlari (on/off)\n"
    "/top — Referral liderlar jadvali\n"
    "/referral — Do'stlarni taklif qilish\n"
    "/premium — Premium xarid / Promokod\n"
    "/history — Oxirgi tekshiruvlar tarixi\n"
    "/report — Xavfli link haqida xabar\n"
    "/feedback — Taklif/shikoyat yuborish\n"
    "/language — Tilni o'zgartirish\n\n"
    "━━━ *Har bir havola tekshiruvida avtomatik* ━━━\n"
    "🎯 Trust Score (0-100) | 🔒 SSL sertifikat | 🔤 Typosquatting\n"
    "🔀 Qisqa havola kengaytirish | 🛠 Texnologiya aniqlash\n"
    "📸 Sayt skrinshoti | 🤖 AI xulosa\n\n"
    "━━━ *Secretary Mode* ━━━\n"
    "🤖 Telegram Business orqali botni ulang → shaxsiy chatlaringiz avtomatik himoyalanadi."
)

TEXTS["ru"]["help_message"] = (
    "📖 *Xavfsizmi? Bot — Все Команды:*\n\n"
    "━━━ *Основные Проверки* ━━━\n"
    "🔗 *Отправить ссылку* — глубокий анализ + Trust Score + вердикт AI\n"
    "📄 *Отправить файл* — APK, PDF, DOC, ZIP, EXE и др. на вирусы\n"
    "📸 *Фото QR-кода* — извлечение и проверка URL\n\n"
    "━━━ *AI Команды* ━━━\n"
    "/ask — AI ответит на вопрос по кибербезопасности\n"
    "/analyze — AI проанализирует подозрительное сообщение/SMS\n\n"
    "━━━ *Проверки* ━━━\n"
    "/breach — Проверка утечки email или пароля\n"
    "/monitor — Постоянный мониторинг email, оповещение при утечке (Премиум)\n"
    "/scammer @username — Проверка аккаунта на мошенничество\n\n"
    "━━━ *Другие Команды* ━━━\n"
    "/phish — Тест друзей на фишинг\n"
    "/tips — Ежедневные советы (on/off)\n"
    "/top — Таблица лидеров рефералов\n"
    "/referral — Пригласить друзей\n"
    "/premium — Купить Premium / Промокод\n"
    "/history — История проверок\n"
    "/report — Сообщить об опасной ссылке\n"
    "/feedback — Обратная связь\n"
    "/language — Сменить язык\n\n"
    "━━━ *При каждой проверке ссылки автоматически* ━━━\n"
    "🎯 Trust Score (0-100) | 🔒 SSL | 🔤 Тайпосквоттинг\n"
    "🔀 Раскрытие коротких ссылок | 🛠 Определение технологий\n"
    "📸 Скриншот сайта | 🤖 Вердикт AI\n\n"
    "━━━ *Режим Секретаря* ━━━\n"
    "🤖 Подключите через Telegram Business → личные чаты автоматически защищены."
)

TEXTS["en"]["help_message"] = (
    "📖 *Xavfsizmi? Bot — All Commands:*\n\n"
    "━━━ *Core Scans* ━━━\n"
    "🔗 *Send a link* — deep analysis + Trust Score + AI verdict\n"
    "📄 *Send a file* — APK, PDF, DOC, ZIP, EXE etc. malware scan\n"
    "📸 *QR code photo* — extract and scan URL inside\n\n"
    "━━━ *AI Commands* ━━━\n"
    "/ask — AI answers your cybersecurity questions\n"
    "/analyze — AI analyzes a suspicious message/SMS\n\n"
    "━━━ *Checks* ━━━\n"
    "/breach — Check if email or password was leaked\n"
    "/monitor — Continuous email monitoring, alerts on new breach (Premium)\n"
    "/scammer @username — Check if an account is a scammer\n\n"
    "━━━ *Other Commands* ━━━\n"
    "/phish — Test your friends with phishing sim\n"
    "/tips — Daily security tips (on/off)\n"
    "/top — Referral leaderboard\n"
    "/referral — Get your invite link\n"
    "/premium — Buy Premium / Promo code\n"
    "/history — Check history\n"
    "/report — Report dangerous link\n"
    "/feedback — Send feedback\n"
    "/language — Change language\n\n"
    "━━━ *Auto-included in every link scan* ━━━\n"
    "🎯 Trust Score (0-100) | 🔒 SSL cert | 🔤 Typosquatting\n"
    "🔀 Short URL expansion | 🛠 Tech detection\n"
    "📸 Website screenshot | 🤖 AI verdict\n\n"
    "━━━ *Secretary Mode* ━━━\n"
    "🤖 Connect via Telegram Business → personal chats auto-protected."
)



# ─── DARK WEB CHECK ───────────────────────────────────────────────────────────

TEXTS["uz"]["darkweb_ask"] = "🕸 *Dark Web Tekshiruvi*\n\nEmail yoki username yuboring — dark web bazalarida borligini tekshiraman:"
TEXTS["ru"]["darkweb_ask"] = "🕸 *Проверка Dark Web*\n\nОтправьте email или username — проверю наличие в базах dark web:"
TEXTS["en"]["darkweb_ask"] = "🕸 *Dark Web Check*\n\nSend an email or username — I'll check dark web databases:"

TEXTS["uz"]["darkweb_found"] = (
    "🕸🚨 *DARK WEB DA TOPILDI!*\n\n"
    "🔍 Tekshirilgan: `{query}`\n"
    "🔴 Topildi: *{count}* ta manbada\n\n"
    "📋 *Topilgan joylar:*\n{sources}\n\n"
    "⚠️ Zudlik bilan parollaringizni o'zgartiring va 2FA yoqing!"
)
TEXTS["ru"]["darkweb_found"] = (
    "🕸🚨 *НАЙДЕНО В DARK WEB!*\n\n"
    "🔍 Проверено: `{query}`\n"
    "🔴 Найдено: в *{count}* источниках\n\n"
    "📋 *Где найдено:*\n{sources}\n\n"
    "⚠️ Срочно смените пароли и включите 2FA!"
)
TEXTS["en"]["darkweb_found"] = (
    "🕸🚨 *FOUND ON DARK WEB!*\n\n"
    "🔍 Checked: `{query}`\n"
    "🔴 Found: in *{count}* sources\n\n"
    "📋 *Found in:*\n{sources}\n\n"
    "⚠️ Immediately change your passwords and enable 2FA!"
)

TEXTS["uz"]["darkweb_safe"] = "🕸✅ *Dark Web Tekshiruvi*\n\n`{query}` dark web bazalarida topilmadi.\n📊 Tekshirilgan: {checked} ta baza\n\n✅ Hozircha xavfsiz. Lekin parollarni muntazam yangilab turing!"
TEXTS["ru"]["darkweb_safe"] = "🕸✅ *Проверка Dark Web*\n\n`{query}` не найдено в базах dark web.\n📊 Проверено: {checked} баз\n\n✅ Пока безопасно. Но регулярно обновляйте пароли!"
TEXTS["en"]["darkweb_safe"] = "🕸✅ *Dark Web Check*\n\n`{query}` was not found in dark web databases.\n📊 Checked: {checked} databases\n\n✅ Safe for now. But keep updating your passwords!"

# ─── PERMISSION EXPLAINER (Premium hint for free users) ───────────────────────

TEXTS["uz"]["perm_premium_hint"] = "Batafsil tushuntirish uchun Premium kerak (/premium)"
TEXTS["ru"]["perm_premium_hint"] = "Для подробного объяснения нужен Premium (/premium)"
TEXTS["en"]["perm_premium_hint"] = "Detailed explanation requires Premium (/premium)"



# ─── BREACH COMBINED REPORT LABELS ────────────────────────────────────────────

TEXTS["uz"]["breach_result_danger"] = "EMAIL XAVF OSTIDA!"
TEXTS["ru"]["breach_result_danger"] = "EMAIL В ОПАСНОСТИ!"
TEXTS["en"]["breach_result_danger"] = "EMAIL COMPROMISED!"

TEXTS["uz"]["breach_result_safe"] = "EMAIL XAVFSIZ"
TEXTS["ru"]["breach_result_safe"] = "EMAIL В БЕЗОПАСНОСТИ"
TEXTS["en"]["breach_result_safe"] = "EMAIL SAFE"

TEXTS["uz"]["breach_section"] = "Ma'lumot sizishlari"
TEXTS["ru"]["breach_section"] = "Утечки данных"
TEXTS["en"]["breach_section"] = "Data breaches"

TEXTS["uz"]["darkweb_section"] = "Dark Web"
TEXTS["ru"]["darkweb_section"] = "Dark Web"
TEXTS["en"]["darkweb_section"] = "Dark Web"

TEXTS["uz"]["breach_action_required"] = "Zudlik bilan parollaringizni o'zgartiring va 2FA yoqing!"
TEXTS["ru"]["breach_action_required"] = "Срочно смените пароли и включите 2FA!"
TEXTS["en"]["breach_action_required"] = "Change your passwords immediately and enable 2FA!"

TEXTS["uz"]["breach_all_clear"] = "Hech qanday sizish yoki dark web mention topilmadi."
TEXTS["ru"]["breach_all_clear"] = "Утечек и упоминаний в dark web не найдено."
TEXTS["en"]["breach_all_clear"] = "No breaches or dark web mentions found."

# ─── UPDATED WELCOME MESSAGE (with all features) ─────────────────────────────

TEXTS["uz"]["start"] = (
    "👋 Salom, *{name}*!\n\n"
    "🛡 *Xavfsizmi?* — sizning kiberxavfsizlik yordamchingiz.\n\n"
    "Menga havola, fayl yoki QR kod yuboring — xavfsizligini tekshiraman.\n\n"
    "━━━ *Buyruqlar* ━━━\n"
    "/help — Barcha buyruqlar\n"
    "/breach — Email/parol tekshirish\n"
    "/ask — AI ga savol berish\n"
    "/analyze — Shubhali xabarni tahlil qilish\n"
    "/scammer — Akkaunt tekshirish\n"
    "/darkweb — Dark web tekshiruvi\n"
    "/monitor — Email monitoring (Premium)\n"
    "/phish — Fishing simulyatori\n"
    "/referral — Do'stlarni taklif qilish\n"
    "/top — Liderlar jadvali\n"
    "/tips — Kunlik maslahatlar\n"
    "/premium — Premium olish\n"
    "/history — Tekshiruvlar tarixi\n"
    "/language — Tilni o'zgartirish\n\n"
    "━━━━━━━━━━━━━━━━\n"
    "📊 Kunlik limit: {limit} ta bepul tekshiruv\n"
    "⭐ Cheksiz → /premium\n"
    "🤖 Secretary rejimi: Telegram → Business → Chatbots"
)

TEXTS["ru"]["start"] = (
    "👋 Привет, *{name}*!\n\n"
    "🛡 *Xavfsizmi?* — ваш помощник по кибербезопасности.\n\n"
    "Отправьте мне ссылку, файл или QR-код — проверю на безопасность.\n\n"
    "━━━ *Команды* ━━━\n"
    "/help — Все команды\n"
    "/breach — Проверка email/пароля\n"
    "/ask — Задать вопрос AI\n"
    "/analyze — Анализ подозрительного сообщения\n"
    "/scammer — Проверка аккаунта\n"
    "/darkweb — Проверка в dark web\n"
    "/monitor — Мониторинг email (Премиум)\n"
    "/phish — Симулятор фишинга\n"
    "/referral — Пригласить друзей\n"
    "/top — Таблица лидеров\n"
    "/tips — Ежедневные советы\n"
    "/premium — Купить Премиум\n"
    "/history — История проверок\n"
    "/language — Сменить язык\n\n"
    "━━━━━━━━━━━━━━━━\n"
    "📊 Лимит: {limit} бесплатных проверок в день\n"
    "⭐ Безлимит → /premium\n"
    "🤖 Режим секретаря: Telegram → Business → Chatbots"
)

TEXTS["en"]["start"] = (
    "👋 Hi, *{name}*!\n\n"
    "🛡 *Xavfsizmi?* — your cybersecurity assistant.\n\n"
    "Send me a link, file, or QR code — I'll check if it's safe.\n\n"
    "━━━ *Commands* ━━━\n"
    "/help — All commands\n"
    "/breach — Check email/password leaks\n"
    "/ask — Ask AI a question\n"
    "/analyze — Analyze a suspicious message\n"
    "/scammer — Check an account\n"
    "/darkweb — Dark web search\n"
    "/monitor — Email monitoring (Premium)\n"
    "/phish — Phishing simulator\n"
    "/referral — Invite friends\n"
    "/top — Leaderboard\n"
    "/tips — Daily security tips\n"
    "/premium — Get Premium\n"
    "/history — Check history\n"
    "/language — Change language\n\n"
    "━━━━━━━━━━━━━━━━\n"
    "📊 Daily limit: {limit} free checks\n"
    "⭐ Unlimited → /premium\n"
    "🤖 Secretary mode: Telegram → Business → Chatbots"
)



# ─── REMAINING HARDCODED STRINGS FIX ──────────────────────────────────────────

TEXTS["uz"]["ai_generating"] = "💡 Maslahat generatsiya qilinmoqda..."
TEXTS["ru"]["ai_generating"] = "💡 Генерирую совет..."
TEXTS["en"]["ai_generating"] = "💡 Generating tip..."

TEXTS["uz"]["admin_premium_off"] = "🔓 Admin Premium o'chirildi. Test mode."
TEXTS["ru"]["admin_premium_off"] = "🔓 Admin Premium отключён. Тестовый режим."
TEXTS["en"]["admin_premium_off"] = "🔓 Admin Premium disabled. Test mode."

TEXTS["uz"]["admin_premium_on"] = "🔒 Admin Premium qayta yoqildi."
TEXTS["ru"]["admin_premium_on"] = "🔒 Admin Premium восстановлен."
TEXTS["en"]["admin_premium_on"] = "🔒 Admin Premium restored."

TEXTS["uz"]["api_error"] = "⚠️ API xatoligi: {error}"
TEXTS["ru"]["api_error"] = "⚠️ Ошибка API: {error}"
TEXTS["en"]["api_error"] = "⚠️ API error: {error}"

TEXTS["uz"]["qr_scan_error"] = "❌ QR-kodni tahlil qilib o'qishda xatolik yuz berdi."
TEXTS["ru"]["qr_scan_error"] = "❌ Ошибка при чтении QR-кода."
TEXTS["en"]["qr_scan_error"] = "❌ Error reading QR code."

TEXTS["uz"]["tips_header"] = "💡 *Kunlik Maslahatlar:* {status}"
TEXTS["ru"]["tips_header"] = "💡 *Ежедневные Советы:* {status}"
TEXTS["en"]["tips_header"] = "💡 *Daily Tips:* {status}"

TEXTS["uz"]["tip_of_day"] = "💡 *Kunlik Xavfsizlik Maslahati:*"
TEXTS["ru"]["tip_of_day"] = "💡 *Совет Дня по Безопасности:*"
TEXTS["en"]["tip_of_day"] = "💡 *Daily Security Tip:*"

TEXTS["uz"]["group_apk_dangerous"] = "🚨 *XAVFLI APK ANIQLANDI!*\n\n👤 {mention}\n📱 Fayl: `{name}`\n{mal}/{total} antivirus xavfli deb topdi!\n⚠️ Bu ilovani O'RNATMANG!"
TEXTS["ru"]["group_apk_dangerous"] = "🚨 *ОБНАРУЖЕН ОПАСНЫЙ APK!*\n\n👤 {mention}\n📱 Файл: `{name}`\n{mal}/{total} антивирусов нашли угрозу!\n⚠️ НЕ устанавливайте!"
TEXTS["en"]["group_apk_dangerous"] = "🚨 *DANGEROUS APK DETECTED!*\n\n👤 {mention}\n📱 File: `{name}`\n{mal}/{total} engines flagged it!\n⚠️ DO NOT install!"

TEXTS["uz"]["group_qr_dangerous"] = "🚨 *XAVFLI QR KOD ANIQLANDI!*\n\n👤 {mention}\n🔗 URL: `{url}`\n⚠️ Bu QR kodga ishonmang!"
TEXTS["ru"]["group_qr_dangerous"] = "🚨 *ОПАСНЫЙ QR-КОД ОБНАРУЖЕН!*\n\n👤 {mention}\n🔗 URL: `{url}`\n⚠️ Не доверяйте этому QR-коду!"
TEXTS["en"]["group_qr_dangerous"] = "🚨 *DANGEROUS QR CODE DETECTED!*\n\n👤 {mention}\n🔗 URL: `{url}`\n⚠️ Don't trust this QR code!"



# ─── TIPS TOGGLE BUTTONS & LABELS ─────────────────────────────────────────────

TEXTS["uz"]["tips_turn_on_btn"] = "✅ Yoqish"
TEXTS["ru"]["tips_turn_on_btn"] = "✅ Включить"
TEXTS["en"]["tips_turn_on_btn"] = "✅ Turn On"

TEXTS["uz"]["tips_turn_off_btn"] = "❌ O'chirish"
TEXTS["ru"]["tips_turn_off_btn"] = "❌ Отключить"
TEXTS["en"]["tips_turn_off_btn"] = "❌ Turn Off"

TEXTS["uz"]["tips_today"] = "Bugungi maslahat"
TEXTS["ru"]["tips_today"] = "Совет дня"
TEXTS["en"]["tips_today"] = "Today's tip"
