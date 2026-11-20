# Translation check: en -> tr (Argos, glossary on)

20 phrases, average 29 ms per phrase on CPU.
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 7 | 55.1 |
| broken | 6 | 48.5 |
| slang | 5 | 37.2 |
| casual | 2 | 56.5 |
| **all** | 20 | **48.8** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | Two are pushing A short, I need help. | İki A short'u itiyor, yardıma ihtiyacım var. | İkisi A short'a basıyor, yardıma ihtiyacım var. | 73 |
| clean | Throw a molly under the car. | Araba altında bir molly fırlatın. | Arabanın altına molly at. | 40 |
| clean | He's hiding in the corner with an AWP. | Bir AWP ile köşede saklanıyor. | Köşede AWP ile saklanıyor. | 71 |
| clean | We have no money, full save this round. | Paramız yok, bu raundu tam olarak kurtarıyoruz. | Paramız yok, bu raunt full save yapalım. | 49 |
| clean | Wait for my flash, then go in together. | Flash için bekleyin, sonra birlikte gidin. | Flash'ımı bekle, sonra birlikte girelim. | 55 |
| clean | The last one is in B site, low HP. | Son olanı B site, canı az. | Sonuncusu B site'ta, canı az. | 41 |
| clean | Don't push mid, hold the angle. | Mid'i zorlama, açısı tut. | Mid'e basma, açıyı tut. | 42 |
| broken | he have AWP, no peek long | AWP'a sahip değil, peek uzun | Onda AWP var, long'a kafa çıkarma. | 9 |
| broken | I no can see, smoke is everywhere | Göremem, smoke her yerde | Göremiyorum, her yer smoke. | 41 |
| broken | why nobody help me, I am alone in B | Neden kimse bana yardım etmedi, sadece B'deyim | Neden kimse yardım etmiyor, B'de yalnızım. | 49 |
| broken | you go mid, me stay here | mid'e gidiyorum, burada kalıyorum | Sen mid'e git, ben burada kalıyorum. | 61 |
| broken | enemy is two, one is very low | Düşman iki, biri çok düşük | Düşman iki kişi, birinin canı çok az. | 41 |
| broken | please not shoot, he is our team | Lütfen ateş etme, o bizim takımımız | Lütfen ateş etme, o bizim takımdan. | 85 |
| slang | gj bro, insane clutch | gj kanka, deli clutch | Eline sağlık kanka, inanılmaz clutch. | 27 |
| slang | ff, they're smurfing | FF, onlar smurfing | Pes edelim, smurf oynuyorlar. | 18 |
| slang | nt guys, ez win next | iyi denemeydi arkadaşlar, kolay bir sonraki kazan | İyi denemeydi arkadaşlar, sonrakini kolay alırız. | 66 |
| slang | he's one tap, push him | O bir dokunuş, onu it | Tek mermilik canı kaldı, üstüne bas. | 6 |
| slang | my bad, I got flashed | benim hatam, I got flashed | Benim hatam, flash yedim. | 52 |
| casual | can you buy me a weapon, I have no money | Beni silah satın alabilir, param yok | Bana silah alabilir misin, param yok. | 53 |
| casual | good job everyone, let's keep going | Herkes iyi bir iş, devam edelim | Herkes iyi iş çıkardı, devam edelim. | 60 |
