# Translation check: en -> tr (Argos)

30 phrases, average 43 ms per phrase on CPU.
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 10 | 29.5 |
| broken | 10 | 49.5 |
| slang | 7 | 14.9 |
| casual | 3 | 29.2 |
| **all** | 30 | **33.8** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | They're rushing B, five of them. | Onlardan beş tanesi acele ediyorlar. | B'ye rush atıyorlar, beşi birden. | 23 |
| clean | One is in A long, he has an AWP. | Biri uzun bir süredir AWP'ye sahiptir. | Biri A long'da, elinde AWP var. | 16 |
| clean | Save your weapon, we can't win this round. | Silahını kurtar, bu turu kazanamayız. | Silahını kurtar, bu raundu kazanamayız. | 79 |
| clean | I'm low, one shot. | Ben düşüküm, bir atış. | Canım az, tek mermilik canım kaldı. | 7 |
| clean | Let's eco this round and full buy next. | Bu turu ekleyelim ve bir sonraki satın alalım. | Bu raunt eco yapalım, sonrakinde full alalım. | 32 |
| clean | Smoke CT and flash for me. | Duman CT ve benim için flaş. | CT'ye smoke at, bana da flash at. | 11 |
| clean | The bomb is planted on A, go retake. | Bomba A'da dikilir, geri alınır. | Bomba A'ya kuruldu, gidip geri alın. | 42 |
| clean | Watch mid, someone is lurking. | Ortayı izleyin, biri lurking. | Orta'ya dikkat et, biri pusuda bekliyor. | 18 |
| clean | Nice try, guys. We'll get the next one. | Nice deneyin, çocuklar. Bir sonrakisini alacağız. | İyi denemeydi arkadaşlar. Sonrakini alırız. | 30 |
| clean | Don't peek, wait for the flash. | peek yapmayın, flaş için bekleyin. | Kafa çıkarma, flash'ı bekle. | 22 |
| broken | he going B, I no have money | B'ye gidiyorum, param yok | B'ye gidiyor, param yok. | 79 |
| broken | why you not drop me weapon | Neden beni silahlamıyorsun | Neden bana silah atmıyorsun? | 51 |
| broken | they is three on A, careful | Onlar A'da üç, dikkatli | A'da üç kişiler, dikkat et. | 41 |
| broken | I am die, sorry, he was behind of box | Ben ölüyorum, üzgünüm, o kutunun arkasındaydı | Öldüm, kusura bakma, kutunun arkasındaydı. | 51 |
| broken | please you buy armor, not only gun | Lütfen zırh satın al, sadece silah değil | Lütfen zırh al, sadece silah değil. | 84 |
| broken | where is bomb? who have bomb? | Bomba nerede? Kim bombaladı? | Bomba nerede? Bomba kimde? | 56 |
| broken | me go A, you go B, okay? | A’ya gidiyorum, B’ye gider misin? | Ben A'ya gidiyorum, sen B'ye git, tamam mı? | 38 |
| broken | enemy very fast, he run to connector | Düşman çok hızlı, takmaya çalışır | Düşman çok hızlı, connector'a koştu. | 46 |
| broken | stop shoot me, I am your team | Beni durdur, senin takımın | Bana ateş etmeyi kes, ben senin takımındanım. | 32 |
| broken | last round we lose because nobody defuse | Son tur kaybettiğimiz için kaybediyoruz çünkü kimse yok | Son raundu kimse bombayı imha etmediği için kaybettik. | 38 |
| slang | nt nt, ez next round | nt, bir sonraki tur | İyi denemeydi, sonraki raunt kolay. | 22 |
| slang | gg wp, they're just better | gg wp, onlar sadece daha iyi | İyi oyundu, onlar daha iyi. | 39 |
| slang | bro he's lit, like 20 hp | 20 hp gibi, | Kanka adamın canı az, 20 can falan. | 3 |
| slang | ninja defuse, go go go | Ninja derme, git git | Gizlice imha et, hadi hadi hadi. | 7 |
| slang | he's baiting, don't swing | Gülüyor, salmıyor | Seni yemliyor, açılma. | 15 |
| slang | rotate rotate, they faked A | döndürmek, sahte A | Dönün dönün, A'ya fake attılar. | 10 |
| slang | my bad, I whiffed | Kötüyüm, I viski | Benim hatam, ıskaladım. | 7 |
| casual | one more round and we win the half | Bir tur daha ve yarıyı kazanıyoruz | Bir raunt daha alırsak devreyi kazanırız. | 25 |
| casual | guys mute that guy, he is crying all game | Erkekler o adamı çiğniyor, tüm oyunu ağlıyor | Arkadaşlar şu adamı susturun, bütün oyun ağlıyor. | 27 |
| casual | can someone drop me AK please | Birisi beni AK'ı bırakabilir lütfen | Biri bana AK atabilir mi lütfen? | 38 |
