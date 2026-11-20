# Translation check: en -> tr (nllb-600m, glossary off)

30 phrases, average 298 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 10 | 30.7 |
| broken | 10 | 51.4 |
| slang | 7 | 17.9 |
| casual | 3 | 56.6 |
| **all** | 30 | **38.5** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | They're rushing B, five of them. | B'ye koştular. Beş kişi. | B'ye rush atıyorlar, beşi birden. | 16 |
| clean | One is in A long, he has an AWP. | Biri A'da uzun, AWP'si var. | Biri A long'da, elinde AWP var. | 27 |
| clean | Save your weapon, we can't win this round. | Silahını koru, bu turda kazanamayız. | Silahını kurtar, bu raundu kazanamayız. | 57 |
| clean | I'm low, one shot. | Düşüm, bir atış. | Canım az, tek mermilik canım kaldı. | 5 |
| clean | Let's eco this round and full buy next. | Bu turda eco yapalım ve bir sonraki tam satın alalım. | Bu raunt eco yapalım, sonrakinde full alalım. | 48 |
| clean | Smoke CT and flash for me. | Sigara çek CT ve benim için flaş. | CT'ye smoke at, bana da flash at. | 11 |
| clean | The bomb is planted on A, go retake. | Bomba A'da yerleştirildi, geri alın. | Bomba A'ya kuruldu, gidip geri alın. | 44 |
| clean | Watch mid, someone is lurking. | Bak orta, biri gizleniyor. | Orta'ya dikkat et, biri pusuda bekliyor. | 22 |
| clean | Nice try, guys. We'll get the next one. | Güzel bir deneme, çocuklar. Bir sonrakiyi alacağız. | İyi denemeydi arkadaşlar. Sonrakini alırız. | 31 |
| clean | Don't peek, wait for the flash. | Bakma, ışığı bekle. | Kafa çıkarma, flash'ı bekle. | 28 |
| broken | he going B, I no have money | B, param yok. | B'ye gidiyor, param yok. | 46 |
| broken | why you not drop me weapon | Neden bana silah bırakmıyorsun? | Neden bana silah atmıyorsun? | 78 |
| broken | they is three on A, careful | A'da üç, dikkatli olun. | A'da üç kişiler, dikkat et. | 41 |
| broken | I am die, sorry, he was behind of box | Ben ölüyorum, üzgünüm, kutu arkasındaydı. | Öldüm, kusura bakma, kutunun arkasındaydı. | 44 |
| broken | please you buy armor, not only gun | Lütfen zırh al, sadece silah değil. | Lütfen zırh al, sadece silah değil. | 100 |
| broken | where is bomb? who have bomb? | Bomba nerede? Kimde bomba var? | Bomba nerede? Bomba kimde? | 60 |
| broken | me go A, you go B, okay? | Ben A, sen B, tamam mı? | Ben A'ya gidiyorum, sen B'ye git, tamam mı? | 35 |
| broken | enemy very fast, he run to connector | Düşman çok hızlı, bağlantıya koştu. | Düşman çok hızlı, connector'a koştu. | 59 |
| broken | stop shoot me, I am your team | Beni vurmayı kes, ben senin takımınım. | Bana ateş etmeyi kes, ben senin takımındanım. | 54 |
| broken | last round we lose because nobody defuse | Son turda kaybediyoruz çünkü kimse cesaret kırıklığına uğramıyor . | Son raundu kimse bombayı imha etmediği için kaybettik. | 23 |
| slang | nt nt, ez next round | nt nt, ez bir sonraki tur | İyi denemeydi, sonraki raunt kolay. | 23 |
| slang | gg wp, they're just better | gg wp, sadece daha iyiler. | İyi oyundu, onlar daha iyi. | 26 |
| slang | bro he's lit, like 20 hp | Dostum, 20 hp gibi yakıyor. | Kanka adamın canı az, 20 can falan. | 7 |
| slang | ninja defuse, go go go | ninja defuse, git git git | Gizlice imha et, hadi hadi hadi. | 7 |
| slang | he's baiting, don't swing | Yumruk yapıyor. Sakın sallanacak değilsin. | Seni yemliyor, açılma. | 14 |
| slang | rotate rotate, they faked A | Dönüştürüyorlar. Dönüştürüyorlar. | Dönün dönün, A'ya fake attılar. | 18 |
| slang | my bad, I whiffed | Benim suçum, kokuladım. | Benim hatam, ıskaladım. | 35 |
| casual | one more round and we win the half | Bir tur daha ve yarısını kazanırız. | Bir raunt daha alırsak devreyi kazanırız. | 37 |
| casual | guys mute that guy, he is crying all game | Çocuklar o adamı susturuyor, bütün oyun boyunca ağlıyor. | Arkadaşlar şu adamı susturun, bütün oyun ağlıyor. | 58 |
| casual | can someone drop me AK please | Biri bana AK bırakabilir mi lütfen ? | Biri bana AK atabilir mi lütfen? | 80 |
