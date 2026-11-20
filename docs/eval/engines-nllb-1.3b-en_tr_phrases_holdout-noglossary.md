# Translation check: en -> tr (nllb-1.3b, glossary off)

20 phrases, average 618 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 7 | 62.9 |
| broken | 6 | 64.1 |
| slang | 5 | 21.5 |
| casual | 2 | 94.8 |
| **all** | 20 | **56.4** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | Two are pushing A short, I need help. | İki kişi kısa basıyor, yardıma ihtiyacım var. | İkisi A short'a basıyor, yardıma ihtiyacım var. | 73 |
| clean | Throw a molly under the car. | Arabanın altına bir molly at. | Arabanın altına molly at. | 84 |
| clean | He's hiding in the corner with an AWP. | Bir AWP ile köşede saklanıyor. | Köşede AWP ile saklanıyor. | 71 |
| clean | We have no money, full save this round. | Paramız yok, bu raundu kurtaralım. | Paramız yok, bu raunt full save yapalım. | 56 |
| clean | Wait for my flash, then go in together. | Işığımı bekle, sonra birlikte gidin. | Flash'ımı bekle, sonra birlikte girelim. | 67 |
| clean | The last one is in B site, low HP. | Sonuncusu B bölgesinde, düşük HP. | Sonuncusu B site'ta, canı az. | 36 |
| clean | Don't push mid, hold the angle. | Ortadan itme, açıyı tut. | Mid'e basma, açıyı tut. | 47 |
| broken | he have AWP, no peek long | O AWP var, uzun bir bakış yok | Onda AWP var, long'a kafa çıkarma. | 23 |
| broken | I no can see, smoke is everywhere | Göremiyorum, her yerde duman var. | Göremiyorum, her yer smoke. | 71 |
| broken | why nobody help me, I am alone in B | Neden kimse bana yardım etmiyor, B'de yalnızım. | Neden kimse yardım etmiyor, B'de yalnızım. | 90 |
| broken | you go mid, me stay here | Sen ortasına git, ben burada kalıyorum. | Sen mid'e git, ben burada kalıyorum. | 74 |
| broken | enemy is two, one is very low | Düşman iki, biri çok düşük. | Düşman iki kişi, birinin canı çok az. | 41 |
| broken | please not shoot, he is our team | Lütfen ateş etmeyin, o bizim takımımız. | Lütfen ateş etme, o bizim takımdan. | 75 |
| slang | gj bro, insane clutch | Kardeşim, çılgın koplama. | Eline sağlık kanka, inanılmaz clutch. | 9 |
| slang | ff, they're smurfing | FF, smurfing yapıyorlar. | Pes edelim, smurf oynuyorlar. | 36 |
| slang | nt guys, ez win next | Çocuklar, sırada EZ kazanıyor. | İyi denemeydi arkadaşlar, sonrakini kolay alırız. | 16 |
| slang | he's one tap, push him | Tek dokunuş, onu it. | Tek mermilik canı kaldı, üstüne bas. | 8 |
| slang | my bad, I got flashed | Benim hatam, bana bir flaş geldi. | Benim hatam, flash yedim. | 49 |
| casual | can you buy me a weapon, I have no money | Bana bir silah alabilir misin, param yok. | Bana silah alabilir misin, param yok. | 90 |
| casual | good job everyone, let's keep going | Herkes iyi iş çıkardı, devam edelim. | Herkes iyi iş çıkardı, devam edelim. | 100 |
