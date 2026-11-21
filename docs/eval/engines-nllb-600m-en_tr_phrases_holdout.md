# Translation check: en -> tr (nllb-600m, glossary on)

20 phrases, average 309 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 7 | 66.9 |
| broken | 6 | 54.0 |
| slang | 5 | 37.1 |
| casual | 2 | 69.8 |
| **all** | 20 | **55.8** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | Two are pushing A short, I need help. | İki kişi A short'u zorluyor, yardıma ihtiyacım var. | İkisi A short'a basıyor, yardıma ihtiyacım var. | 71 |
| clean | Throw a molly under the car. | Molly'yi arabanın altına at. | Arabanın altına molly at. | 64 |
| clean | He's hiding in the corner with an AWP. | Bir AWP ile köşede saklanıyor. | Köşede AWP ile saklanıyor. | 71 |
| clean | We have no money, full save this round. | Raunttan başka paramız yok. | Paramız yok, bu raunt full save yapalım. | 32 |
| clean | Wait for my flash, then go in together. | Flash'imi bekle, sonra birlikte gidin. | Flash'ımı bekle, sonra birlikte girelim. | 68 |
| clean | The last one is in B site, low HP. | Sonuncusu B site, canı az. | Sonuncusu B site'ta, canı az. | 77 |
| clean | Don't push mid, hold the angle. | Mid'e basma, açıyı tut. | Mid'e basma, açıyı tut. | 100 |
| broken | he have AWP, no peek long | AWP, peek değil. | Onda AWP var, long'a kafa çıkarma. | 7 |
| broken | I no can see, smoke is everywhere | Smoke her yerde. | Göremiyorum, her yer smoke. | 28 |
| broken | why nobody help me, I am alone in B | Neden kimse bana yardım etmiyor, B'de yalnızım. | Neden kimse yardım etmiyor, B'de yalnızım. | 90 |
| broken | you go mid, me stay here | Sen mid, ben burada kalırım. | Sen mid'e git, ben burada kalıyorum. | 57 |
| broken | enemy is two, one is very low | Düşman iki, biri çok düşük. | Düşman iki kişi, birinin canı çok az. | 41 |
| broken | please not shoot, he is our team | Lütfen ateş etmeyin, o bizim takımımız. | Lütfen ateş etme, o bizim takımdan. | 75 |
| slang | gj bro, insane clutch | GG kanka, deli clutch | Eline sağlık kanka, inanılmaz clutch. | 27 |
| slang | ff, they're smurfing | FF, sürfediyorlar. | Pes edelim, smurf oynuyorlar. | 27 |
| slang | nt guys, ez win next | iyi denemeydi arkadaşlar, bir sonraki kazanım kolay. | İyi denemeydi arkadaşlar, sonrakini kolay alırız. | 66 |
| slang | he's one tap, push him | O bir dokunuş, onu it. | Tek mermilik canı kaldı, üstüne bas. | 6 |
| slang | my bad, I got flashed | benim hatam, gözüm açıldı. | Benim hatam, flash yedim. | 41 |
| casual | can you buy me a weapon, I have no money | Bana bir silah alabilir misin, param yok. | Bana silah alabilir misin, param yok. | 90 |
| casual | good job everyone, let's keep going | İyi iş, devam edelim. | Herkes iyi iş çıkardı, devam edelim. | 46 |
