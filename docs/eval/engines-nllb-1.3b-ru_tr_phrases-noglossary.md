# Translation check: ru -> tr (nllb-1.3b, glossary off)

20 phrases, average 557 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| callout | 11 | 40.4 |
| slang | 4 | 35.9 |
| casual | 5 | 50.5 |
| **all** | 20 | **42.1** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| callout | Они идут на Б, их трое. | B'ye gidiyorlar, üçü. | B'ye geliyorlar, üç kişiler. | 47 |
| callout | Один на мидле с авп. | Ortalarda bir tane var. | Mid'de bir kişi var, elinde AWP var. | 14 |
| callout | У меня нет денег, давайте эко. | Param yok, ekona gidelim. | Param yok, eco yapalım. | 46 |
| callout | Кинь мне флешку. | Bırak o belleği. | Bana flash at. | 5 |
| callout | Бомба на А, идём ретейкать. | Bomba A'da, konuşalım. | Bomba A'da, retake'e gidiyoruz. | 34 |
| callout | Последний на Б, он почти мёртвый. | Sonuncusu B'de, neredeyse ölü. | Sonuncusu B'de, neredeyse ölü. | 100 |
| callout | Не пикай, жди флешку. | Çişme, fleşeyi bekle. | Kafa çıkarma, flash'ı bekle. | 21 |
| callout | Я его добил, минус один. | Onu öldürdüm, -1. | Onu bitirdim, bir eksik. | 11 |
| slang | Скинь мне калаш, пожалуйста. | Kalahımı çıkar, lütfen. | Bana AK atar mısın lütfen. | 31 |
| slang | Ротейтимся на А, они фейканули. | A'ya dönüyoruz, bozuldular. | A'ya dönüyoruz, fake attılar. | 56 |
| casual | Хорошая попытка, следующий раунд наш. | İyi deneme, bir sonraki raunt bizim. | İyi denemeydi, sonraki raunt bizim. | 78 |
| casual | Пацаны, играем спокойно. | Çocuklar, sakin olun. | Beyler, sakin oynuyoruz. | 33 |
| slang | Он с дигла меня убил. | Beni kazıkla öldürdü. | Beni Deagle ile öldürdü. | 40 |
| slang | Смок на кт, я захожу. | Kahretsin, içeri gireceğim. | CT'ye smoke, giriyorum. | 12 |
| callout | Двое на шорте, осторожно. | Şortlu iki kişi, dikkatli olun. | Short'ta iki kişi var, dikkat. | 42 |
| casual | Блин, я промахнулся. | Lanet olsun, kaçırdım. | Kahretsin, ıskaladım. | 21 |
| callout | Кто разминирует? | Kim temizleyecek? | Kim imha ediyor? | 14 |
| callout | Сейв, этот раунд не выиграем. | Sev, bu raundu kazanamayız. | Silahını kurtar, bu raundu kazanamayız. | 61 |
| casual | Хорошая игра, ребята. | İyi oyunlar, çocuklar. | İyi oyundu arkadaşlar. | 38 |
| casual | Не стреляй в меня, я свой. | Bana ateş etme, ben senin adamım. | Bana ateş etme, ben takımdanım. | 62 |
