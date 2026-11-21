# Translation check: en -> tr (nllb-1.3b, glossary on)

20 phrases, average 735 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 7 | 68.7 |
| broken | 6 | 66.7 |
| slang | 5 | 38.9 |
| casual | 2 | 94.8 |
| **all** | 20 | **63.5** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | Two are pushing A short, I need help. | İki kişi A short'u itiyor, yardıma ihtiyacım var. | İkisi A short'a basıyor, yardıma ihtiyacım var. | 72 |
| clean | Throw a molly under the car. | Arabanın altına bir molly at. | Arabanın altına molly at. | 84 |
| clean | He's hiding in the corner with an AWP. | Bir AWP ile köşede saklanıyor. | Köşede AWP ile saklanıyor. | 71 |
| clean | We have no money, full save this round. | Paramız yok, bu raundu kurtaralım. | Paramız yok, bu raunt full save yapalım. | 56 |
| clean | Wait for my flash, then go in together. | Flash'imi bekle, sonra birlikte gidin. | Flash'ımı bekle, sonra birlikte girelim. | 68 |
| clean | The last one is in B site, low HP. | Sonuncusu B site, canı az. | Sonuncusu B site'ta, canı az. | 77 |
| clean | Don't push mid, hold the angle. | Mid'i itme, açıyı tut. | Mid'e basma, açıyı tut. | 53 |
| broken | he have AWP, no peek long | AWP, peek uzun değil. | Onda AWP var, long'a kafa çıkarma. | 8 |
| broken | I no can see, smoke is everywhere | Göremiyorum, smoke her yerde. | Göremiyorum, her yer smoke. | 71 |
| broken | why nobody help me, I am alone in B | Neden kimse bana yardım etmiyor, B'de yalnızım. | Neden kimse yardım etmiyor, B'de yalnızım. | 90 |
| broken | you go mid, me stay here | Sen mid'e git, ben burada kalıyorum. | Sen mid'e git, ben burada kalıyorum. | 100 |
| broken | enemy is two, one is very low | Düşman iki, biri çok düşük. | Düşman iki kişi, birinin canı çok az. | 41 |
| broken | please not shoot, he is our team | Lütfen ateş etmeyin, o bizim takımımız. | Lütfen ateş etme, o bizim takımdan. | 75 |
| slang | gj bro, insane clutch | kanka, çılgın clutch | Eline sağlık kanka, inanılmaz clutch. | 28 |
| slang | ff, they're smurfing | FF, smurf oluyorlar. | Pes edelim, smurf oynuyorlar. | 45 |
| slang | nt guys, ez win next | iyi denemeydi arkadaşlar, sırada kolay bir zafer. | İyi denemeydi arkadaşlar, sonrakini kolay alırız. | 60 |
| slang | he's one tap, push him | Tek dokunuş, onu it. | Tek mermilik canı kaldı, üstüne bas. | 8 |
| slang | my bad, I got flashed | benim hatam, yanıp söndüm. | Benim hatam, flash yedim. | 43 |
| casual | can you buy me a weapon, I have no money | Bana bir silah alabilir misin, param yok. | Bana silah alabilir misin, param yok. | 90 |
| casual | good job everyone, let's keep going | Herkes iyi iş çıkardı, devam edelim. | Herkes iyi iş çıkardı, devam edelim. | 100 |
