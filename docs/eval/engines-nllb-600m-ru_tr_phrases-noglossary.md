# Translation check: ru -> tr (nllb-600m, glossary off)

20 phrases, average 257 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| callout | 11 | 38.1 |
| slang | 4 | 26.1 |
| casual | 5 | 40.8 |
| **all** | 20 | **36.5** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| callout | Они идут на Б, их трое. | B'ye gidiyorlar, üçü. | B'ye geliyorlar, üç kişiler. | 47 |
| callout | Один на мидле с авп. | Avp'den bir tane. | Mid'de bir kişi var, elinde AWP var. | 11 |
| callout | У меня нет денег, давайте эко. | Param yok, ekzo yapalım. | Param yok, eco yapalım. | 78 |
| callout | Кинь мне флешку. | Bana bir flash at. | Bana flash at. | 68 |
| callout | Бомба на А, идём ретейкать. | Bomba A'ya, geri dönüyoruz. | Bomba A'da, retake'e gidiyoruz. | 37 |
| callout | Последний на Б, он почти мёртвый. | B'deki son kişi neredeyse öldü. | Sonuncusu B'de, neredeyse ölü. | 45 |
| callout | Не пикай, жди флешку. | Sıkma, şarjı bekle. | Kafa çıkarma, flash'ı bekle. | 30 |
| callout | Я его добил, минус один. | Onu aldım, bir eksi. | Onu bitirdim, bir eksik. | 43 |
| slang | Скинь мне калаш, пожалуйста. | Bana kaş atın, lütfen. | Bana AK atar mısın lütfen. | 37 |
| slang | Ротейтимся на А, они фейканули. | A'ya geçelim, onlar siktir oldular. | A'ya dönüyoruz, fake attılar. | 19 |
| casual | Хорошая попытка, следующий раунд наш. | İyi bir girişim. Bir sonraki atış bizim. | İyi denemeydi, sonraki raunt bizim. | 33 |
| casual | Пацаны, играем спокойно. | Çocuklar, sakin oynayalım. | Beyler, sakin oynuyoruz. | 41 |
| slang | Он с дигла меня убил. | Beni öldürdü. | Beni Deagle ile öldürdü. | 41 |
| slang | Смок на кт, я захожу. | Bir ejderha, içeri gireceğim. | CT'ye smoke, giriyorum. | 12 |
| callout | Двое на шорте, осторожно. | İki şort, dikkatli olun. | Short'ta iki kişi var, dikkat. | 29 |
| casual | Блин, я промахнулся. | Kahretsin, hata yaptım. | Kahretsin, ıskaladım. | 49 |
| callout | Кто разминирует? | Kim karıştırıyor? | Kim imha ediyor? | 21 |
| callout | Сейв, этот раунд не выиграем. | Sev, bu turda kazanamayacağız. | Silahını kurtar, bu raundu kazanamayız. | 31 |
| casual | Хорошая игра, ребята. | Güzel bir oyun, çocuklar. | İyi oyundu arkadaşlar. | 20 |
| casual | Не стреляй в меня, я свой. | Bana ateş etme, ben de kendimimim. | Bana ateş etme, ben takımdanım. | 58 |
