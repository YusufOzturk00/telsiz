# Translation check: en -> tr (nllb-600m, glossary off)

20 phrases, average 288 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 7 | 49.6 |
| broken | 6 | 60.4 |
| slang | 5 | 15.1 |
| casual | 2 | 69.8 |
| **all** | 20 | **46.5** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | Two are pushing A short, I need help. | İki kişi kısa bir adım atıyor. Yardım lazım. | İkisi A short'a basıyor, yardıma ihtiyacım var. | 22 |
| clean | Throw a molly under the car. | Arabanın altına bir molly at. | Arabanın altına molly at. | 84 |
| clean | He's hiding in the corner with an AWP. | Bir AWP ile köşede saklanıyor. | Köşede AWP ile saklanıyor. | 71 |
| clean | We have no money, full save this round. | Paramız yok, bu turdan daha fazlası var. | Paramız yok, bu raunt full save yapalım. | 41 |
| clean | Wait for my flash, then go in together. | Benim flaşımı bekle, sonra birlikte gidin. | Flash'ımı bekle, sonra birlikte girelim. | 67 |
| clean | The last one is in B site, low HP. | Sonuncusu B bölgesinde, düşük HP. | Sonuncusu B site'ta, canı az. | 36 |
| clean | Don't push mid, hold the angle. | Ortalığı itme, açıyı tut. | Mid'e basma, açıyı tut. | 45 |
| broken | he have AWP, no peek long | AWP'si var, hiç bakmıyor. | Onda AWP var, long'a kafa çıkarma. | 16 |
| broken | I no can see, smoke is everywhere | Göremiyorum, her yerde duman var. | Göremiyorum, her yer smoke. | 71 |
| broken | why nobody help me, I am alone in B | Neden kimse bana yardım etmiyor, B'de yalnızım. | Neden kimse yardım etmiyor, B'de yalnızım. | 90 |
| broken | you go mid, me stay here | Sen yarıya git, ben burada kalırım. | Sen mid'e git, ben burada kalıyorum. | 58 |
| broken | enemy is two, one is very low | Düşman iki, biri çok düşük. | Düşman iki kişi, birinin canı çok az. | 41 |
| broken | please not shoot, he is our team | Lütfen ateş etmeyin, o bizim takımımız. | Lütfen ateş etme, o bizim takımdan. | 75 |
| slang | gj bro, insane clutch | Dostum, çılgın kablo. | Eline sağlık kanka, inanılmaz clutch. | 9 |
| slang | ff, they're smurfing | Fff, onlar smurf ediyorlar | Pes edelim, smurf oynuyorlar. | 31 |
| slang | nt guys, ez win next | Çocuklar, bir dahaki seferi kazanmayın. | İyi denemeydi arkadaşlar, sonrakini kolay alırız. | 17 |
| slang | he's one tap, push him | O bir dokunuş, onu it. | Tek mermilik canı kaldı, üstüne bas. | 6 |
| slang | my bad, I got flashed | Bu benim suçum. | Benim hatam, flash yedim. | 13 |
| casual | can you buy me a weapon, I have no money | Bana bir silah alabilir misin, param yok. | Bana silah alabilir misin, param yok. | 90 |
| casual | good job everyone, let's keep going | İyi iş, devam edelim. | Herkes iyi iş çıkardı, devam edelim. | 46 |
