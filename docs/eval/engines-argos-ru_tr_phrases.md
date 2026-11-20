# Translation check: ru -> tr (argos, glossary on)

20 phrases, average 90 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| callout | 11 | 28.7 |
| slang | 4 | 38.2 |
| casual | 5 | 23.3 |
| **all** | 20 | **29.2** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| callout | Они идут на Б, их трое. | B'ye giderler, üçü. | B'ye geliyorlar, üç kişiler. | 26 |
| callout | Один на мидле с авп. | Bir awp ile ortadaki biri. | Mid'de bir kişi var, elinde AWP var. | 12 |
| callout | У меня нет денег, давайте эко. | Param yok, eco gidelim. | Param yok, eco yapalım. | 57 |
| callout | Кинь мне флешку. | Beni bir flaş sürücüsü fırlatın. | Bana flash at. | 15 |
| callout | Бомба на А, идём ретейкать. | A'daki bomba, alalım. | Bomba A'da, retake'e gidiyoruz. | 18 |
| callout | Последний на Б, он почти мёртвый. | B'de son olarak neredeyse öldü. | Sonuncusu B'de, neredeyse ölü. | 45 |
| callout | Не пикай, жди флешку. | Not beep, flaş sürücü için bekleyin. | Kafa çıkarma, flash'ı bekle. | 19 |
| callout | Я его добил, минус один. | Ben bitirdim, eksi bir tane. | Onu bitirdim, bir eksik. | 48 |
| slang | Скинь мне калаш, пожалуйста. | Bana kalash ver, lütfen. | Bana AK atar mısın lütfen. | 34 |
| slang | Ротейтимся на А, они фейканули. | A'da Rotate, sahte yaptılar. | A'ya dönüyoruz, fake attılar. | 24 |
| casual | Хорошая попытка, следующий раунд наш. | Nice deneyin, bir sonraki tur bizimdir. | İyi denemeydi, sonraki raunt bizim. | 37 |
| casual | Пацаны, играем спокойно. | Guys, sessizce oynayın. | Beyler, sakin oynuyoruz. | 16 |
| slang | Он с дигла меня убил. | Beni bir Digla ile öldürdü. | Beni Deagle ile öldürdü. | 57 |
| slang | Смок на кт, я захожу. | Duman, içeri giriyorum. | CT'ye smoke, giriyorum. | 42 |
| callout | Двое на шорте, осторожно. | Kısa, dikkatli. | Short'ta iki kişi var, dikkat. | 23 |
| casual | Блин, я промахнулся. | Adam, özledim. | Kahretsin, ıskaladım. | 8 |
| callout | Кто разминирует? | Kim mayınları temizler? | Kim imha ediyor? | 17 |
| callout | Сейв, этот раунд не выиграем. | Kaydet, bu turu kazanamayacağız. | Silahını kurtar, bu raundu kazanamayız. | 34 |
| casual | Хорошая игра, ребята. | İyi oyun, çocuklar. | İyi oyundu arkadaşlar. | 37 |
| casual | Не стреляй в меня, я свой. | Beni vurmayın, benimkiyim. | Bana ateş etme, ben takımdanım. | 14 |
