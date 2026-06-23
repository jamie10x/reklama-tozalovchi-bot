# Flagged Message Keywords

This file documents the keyword and pattern signals the bot uses to flag chat messages.

Sources:
- Advertisement phrase matching: `app/detector/phrases.py`
- Security/threat phrase matching: `app/detector/security.py`
- Pattern indicators: `app/detector/extractor.py`

## Advertisement Phrases

### English Telegram Invite

- join our channel
- join my channel
- subscribe now
- subscribe to
- join our group
- check out my channel
- use this bot
- subscribe for more
- join us
- join here

### English Commercial

- buy now
- buy cheap
- limited offer
- special offer
- limited time
- check out
- contact me
- dm me
- message me
- cheap price
- discount
- promotion service
- advertising service
- earn money
- guaranteed profit
- investment opportunity
- referral link
- use my referral
- dm for price
- dm for details
- message for price
- contact for price
- price

### Uzbek Commercial

- ёғ
- ёғлар
- ёғдан
- ёғни
- қорин
- вазн
- ортиқча вазн
- вазн йўқотиш
- ариқлаш
- кет
- кетказиш
- кетказин
- минус
- кило
- капсула
- таблетка
- препарат
- дори
- восита
- мўъжиза
- мўъжизавий
- тезкор
- тез натижа
- осон
- осон йўл
- кафолат
- 100% кафолат
- натижа
- алоҳида таклиф
- таклиф
- акция
- чегирма
- арзон
- нарх
- доставка
- буюртма
- буюртма беринг
- ёзинг
- мурожаат
- мурожаат қилинг
- телефон
- сайт
- ссылк
- силка
- берди
- кун
- кунда
- хабар
- хабар беринг
- sotuv
- sotib olish
- chegirma
- yetkazib berish
- buyurtma

### Russian Commercial

- жир
- похуд
- вес
- лишний вес
- капсул
- таблетк
- препарат
- средств
- чудо
- чудодейственн
- быстр
- моментальн
- результат
- гаранти
- 100% гарантия
- скидк
- акци
- цена
- дешев
- доставк
- заказ
- купить
- заказать
- предложени
- специальное предложени
- успей
- ограниченно
- бесплат
- оплата
- переход
- ссылк
- перейди
- подпишись
- напиши
- свяжись
- контакт
- телефон
- сайт
- промокод
- секрет
- уникальн

## Security Phrases

### Uzbek Scam

- pul ishlash
- tez pul
- oson pul
- kafolatlangan daromad
- investitsiya
- sarmoya kiriting
- foyda olasiz
- promokod
- bonus oling
- yutuq chiqdi
- sovrin yutdingiz
- plastik karta
- pul mukofot
- mukofot bor
- karta raqamingiz
- karta nomer
- kartangizni yuboring
- click orqali
- payme orqali
- ishonchli daromad
- kripto sarmoya
- pul tikib
- foyda kafolat

### Uzbek Phishing

- kodni yuboring
- sms kod
- tasdiqlash kodi
- akkauntni tiklash
- parolni yuboring
- havolaga kiring
- linkka kiring
- kabinetga kiring
- parol kodini
- karta parol
- telegram kod
- login kod
- akkaunt tasdiqlash

### Uzbek Drug/Medical

- retseptsiz
- kuchli dori
- maxfiy dori
- garantiya natija
- ozdiruvchi
- oriqlash
- jinsiy quvvat
- potensiya
- narkotik
- giyohvand
- marixuana
- geroin
- tropikamid

### Uzbek Gambling

- stavka
- tikish
- bukmeker
- kazino
- slot
- totalizator
- aniq prognoz
- express stavka
- 1xbet
- mostbet
- melbet

### Uzbek Fake Job

- uyda ish
- kunlik to'lov
- kunlik daromad
- tajriba shart emas
- pasport kerak
- karta ochish
- nomingizga karta
- operator kerak

### Uzbek Violence

- qurol sotiladi
- portlovchi
- urishamiz
- o'ldirish
- qo'rqitish
- pichoq sotiladi
- travmatik
- patron

### Uzbek Cyrillic Scam

- пул ишлаш
- тез пул
- осон пул
- кафолатланган даромад
- инвестиция
- сармоя киритинг
- фойда оласиз
- ютуқ чиқди
- соврин ютдингиз
- пластик карта

### Uzbek Cyrillic Phishing

- кодни юборинг
- смс код
- тасдиқлаш коди
- аккаунтни тиклаш
- паролни юборинг
- ҳаволага киринг
- линкка киринг

### Uzbek Cyrillic Drug/Medical

- рецептсиз
- кучли дори
- махфий дори
- гарантия натижа
- оздирувчи
- ориқлаш
- жинсий қувват
- потенция
- наркотик
- гиёҳванд

### Uzbek Cyrillic Gambling

- ставка
- тикиш
- букмекер
- казино
- слот
- тотализатор
- аниқ прогноз

### Uzbek Cyrillic Fake Job

- уйда иш
- кунлик тўлов
- кунлик даромад
- тажриба шарт эмас
- паспорт керак
- карта очиш
- номингизга карта

### Uzbek Cyrillic Violence

- қурол сотилади
- портловчи
- ўлдириш
- қўрқитиш

### English Scam

- guaranteed profit
- double your money
- quick money
- investment opportunity
- claim prize
- you won
- send deposit
- risk free profit

### English Phishing

- send code
- verification code
- login link
- recover account
- confirm your wallet
- seed phrase
- private key
- otp code

### English Drug/Medical

- no prescription
- miracle cure
- weight loss pills
- potency pills

### English Gambling

- casino bonus
- sports betting
- bet now
- fixed match
- sure odds

### English Fake Job

- work from home
- daily payout
- no experience needed
- open card

### English Violence

- weapon for sale
- explosive
- kill threat
- shooting

### Russian Scam

- быстрые деньги
- легкий заработок
- гарантированный доход
- инвестиция
- удвоим деньги
- вы выиграли
- получить приз

### Russian Phishing

- отправьте код
- смс код
- код подтверждения
- восстановить аккаунт
- сид фраза
- приватный ключ
- перейдите по ссылке

### Russian Drug/Medical

- без рецепта
- чудо средство
- таблетки для похудения
- потенция
- секретный препарат
- наркотик

### Russian Gambling

- ставки
- букмекер
- казино
- слоты
- договорной матч

### Russian Fake Job

- работа на дому
- ежедневная оплата
- без опыта
- оформить карту

### Russian Violence

- продам оружие
- взрывчатка
- угроза убийством

## Pattern Indicators

The bot also flags messages that contain these extracted patterns:

- URLs starting with `http://` or `https://`
- Telegram mentions like `@username`
- Telegram invite/link domains: `t.me`, `telegram.me`, `telegram.dog`
- Referral or tracking parameters in URLs
- IPv4 addresses
- BTC, ETH, and TRX wallet addresses
- Phone numbers
- Email addresses
- Forwarded messages from unrelated channels
