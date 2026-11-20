# Translation check: en -> tr (Argos, glossary on)

30 phrases, average 55 ms per phrase on CPU.
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 10 | 37.5 |
| broken | 10 | 50.3 |
| slang | 7 | 47.7 |
| casual | 3 | 29.3 |
| **all** | 30 | **42.9** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | They're rushing B, five of them. | Onlardan beş tanesi acele ediyorlar. | B'ye rush atıyorlar, beşi birden. | 23 |
| clean | One is in A long, he has an AWP. | Biri A long'de, bir AWP var. | Biri A long'da, elinde AWP var. | 59 |
| clean | Save your weapon, we can't win this round. | Silahını kurtar, bu turu kazanamayız. | Silahını kurtar, bu raundu kazanamayız. | 79 |
| clean | I'm low, one shot. | Ben düşüküm tek mermilik. | Canım az, tek mermilik canım kaldı. | 35 |
| clean | Let's eco this round and full buy next. | Eco bu tur ve full buy bir sonraki. | Bu raunt eco yapalım, sonrakinde full alalım. | 25 |
| clean | Smoke CT and flash for me. | Smoke CT ve flash benim için. | CT'ye smoke at, bana da flash at. | 21 |
| clean | The bomb is planted on A, go retake. | Bomba kuruldu A'da, retake'ye gidin. | Bomba A'ya kuruldu, gidip geri alın. | 39 |
| clean | Watch mid, someone is lurking. | Mid'i izleyin, biri lurking. | Orta'ya dikkat et, biri pusuda bekliyor. | 13 |
| clean | Nice try, guys. We'll get the next one. | İyi denemeydi, çocuklar. Bir sonrakisini alacağız. | İyi denemeydi arkadaşlar. Sonrakini alırız. | 49 |
| clean | Don't peek, wait for the flash. | Peek beklemeyin, flash için bekleyin. | Kafa çıkarma, flash'ı bekle. | 27 |
| broken | he going B, I no have money | B'ye gidiyorum, param yok | B'ye gidiyor, param yok. | 79 |
| broken | why you not drop me weapon | Neden beni silahlamıyorsun | Neden bana silah atmıyorsun? | 51 |
| broken | they is three on A, careful | Onlar A'da üç, dikkatli | A'da üç kişiler, dikkat et. | 41 |
| broken | I am die, sorry, he was behind of box | Ben ölüyorum, üzgünüm, o kutunun arkasındaydı | Öldüm, kusura bakma, kutunun arkasındaydı. | 51 |
| broken | please you buy armor, not only gun | Lütfen zırh satın al, sadece silah değil | Lütfen zırh al, sadece silah değil. | 84 |
| broken | where is bomb? who have bomb? | Bomba nerede? Kim bombaladı? | Bomba nerede? Bomba kimde? | 56 |
| broken | me go A, you go B, okay? | A’ya gidiyorum, B’ye gider misin? | Ben A'ya gidiyorum, sen B'ye git, tamam mı? | 38 |
| broken | enemy very fast, he run to connector | Düşman çok hızlı, connector'e gidiyor | Düşman çok hızlı, connector'a koştu. | 76 |
| broken | stop shoot me, I am your team | Beni durdur, senin takımın | Bana ateş etmeyi kes, ben senin takımındanım. | 32 |
| broken | last round we lose because nobody defuse | Son tur kaybediyoruz çünkü kimse defuse | Son raundu kimse bombayı imha etmediği için kaybettik. | 21 |
| slang | nt nt, ez next round | iyi denemeydi iyi denemeydi, bir sonraki tur kolay | İyi denemeydi, sonraki raunt kolay. | 55 |
| slang | gg wp, they're just better | iyi oyundu iyi oynadınız, onlar sadece daha iyi | İyi oyundu, onlar daha iyi. | 55 |
| slang | bro he's lit, like 20 hp | bro adamın canı az, 20 can gibi | Kanka adamın canı az, 20 can falan. | 60 |
| slang | ninja defuse, go go go | ninja defuse, hadi hadi hadi | Gizlice imha et, hadi hadi hadi. | 46 |
| slang | he's baiting, don't swing | Gülüyor, swing | Seni yemliyor, açılma. | 12 |
| slang | rotate rotate, they faked A | rotate rotate, onlar sahte A | Dönün dönün, A'ya fake attılar. | 10 |
| slang | my bad, I whiffed | benim hatam, ıskaladım | Benim hatam, ıskaladım. | 90 |
| casual | one more round and we win the half | Bir tur daha ve yarıyı kazanıyoruz | Bir raunt daha alırsak devreyi kazanırız. | 25 |
| casual | guys mute that guy, he is crying all game | Erkekler o adamı çiğniyor, tüm oyunu ağlıyor | Arkadaşlar şu adamı susturun, bütün oyun ağlıyor. | 27 |
| casual | can someone drop me AK please | Birisi beni AK bırakabilir lütfen | Biri bana AK atabilir mi lütfen? | 39 |
