# Translation check: en -> tr (nllb-1.3b, glossary on)

30 phrases, average 670 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 10 | 55.6 |
| broken | 10 | 57.8 |
| slang | 7 | 67.3 |
| casual | 3 | 68.1 |
| **all** | 30 | **60.1** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | They're rushing B, five of them. | Rush atıyorlarB, beş tane. | B'ye rush atıyorlar, beşi birden. | 46 |
| clean | One is in A long, he has an AWP. | Biri A long'da, o da AWP'ta. | Biri A long'da, elinde AWP var. | 52 |
| clean | Save your weapon, we can't win this round. | Silahını kurtar, bu raundu kazanamayız. | Silahını kurtar, bu raundu kazanamayız. | 100 |
| clean | I'm low, one shot. | Canım az, tek mermilik. | Canım az, tek mermilik canım kaldı. | 65 |
| clean | Let's eco this round and full buy next. | Eco yapalım bu raunt ve sırada full buy. | Bu raunt eco yapalım, sonrakinde full alalım. | 36 |
| clean | Smoke CT and flash for me. | Smoke CT ve flash benim için. | CT'ye smoke at, bana da flash at. | 21 |
| clean | The bomb is planted on A, go retake. | A'da bomba kuruldu, retake'e geç. | Bomba A'ya kuruldu, gidip geri alın. | 34 |
| clean | Watch mid, someone is lurking. | Mid, pusuda bekliyor izleyin. | Orta'ya dikkat et, biri pusuda bekliyor. | 42 |
| clean | Nice try, guys. We'll get the next one. | İyi denemeydi, arkadaşlar. Bir sonrakini alacağız. | İyi denemeydi arkadaşlar. Sonrakini alırız. | 70 |
| clean | Don't peek, wait for the flash. | Kafa çıkarma, flash'i bekle. | Kafa çıkarma, flash'ı bekle. | 84 |
| broken | he going B, I no have money | B, param yok. | B'ye gidiyor, param yok. | 46 |
| broken | why you not drop me weapon | Neden silahımı bırakmıyorsun ? | Neden bana silah atmıyorsun? | 50 |
| broken | they is three on A, careful | A'da üç. Dikkatli olun. | A'da üç kişiler, dikkat et. | 31 |
| broken | I am die, sorry, he was behind of box | Öldüm, üzgünüm, kutu arkasındaydı. | Öldüm, kusura bakma, kutunun arkasındaydı. | 51 |
| broken | please you buy armor, not only gun | Lütfen zırh al, sadece silah değil. | Lütfen zırh al, sadece silah değil. | 100 |
| broken | where is bomb? who have bomb? | Bomba nerede? Kimde bomba var? | Bomba nerede? Bomba kimde? | 60 |
| broken | me go A, you go B, okay? | Ben A, sen B, tamam mı? | Ben A'ya gidiyorum, sen B'ye git, tamam mı? | 35 |
| broken | enemy very fast, he run to connector | Düşman çok hızlı, connector'a koştu. | Düşman çok hızlı, connector'a koştu. | 100 |
| broken | stop shoot me, I am your team | Beni vurmayı kes, ben senin takımınım. | Bana ateş etmeyi kes, ben senin takımındanım. | 54 |
| broken | last round we lose because nobody defuse | Son raundu kaybettik çünkü kimse defuse'u kaybetmedi. | Son raundu kimse bombayı imha etmediği için kaybettik. | 47 |
| slang | nt nt, ez next round | iyi denemeydi iyi denemeydi, kolay bir sonraki raunt | İyi denemeydi, sonraki raunt kolay. | 68 |
| slang | gg wp, they're just better | iyi oyundu iyi oynadınız, sadece daha iyiler. | İyi oyundu, onlar daha iyi. | 46 |
| slang | bro he's lit, like 20 hp | kanka adamın canı az, 20 can gibi | Kanka adamın canı az, 20 can falan. | 75 |
| slang | ninja defuse, go go go | ninja defuse, hadi hadi hadi | Gizlice imha et, hadi hadi hadi. | 46 |
| slang | he's baiting, don't swing | seni yemliyor, açılma | Seni yemliyor, açılma. | 89 |
| slang | rotate rotate, they faked A | dönün dönün, fake attılar A | Dönün dönün, A'ya fake attılar. | 67 |
| slang | my bad, I whiffed | benim hatam, ıskaladım | Benim hatam, ıskaladım. | 90 |
| casual | one more round and we win the half | Bir raunt daha ve yarısını kazanırız . | Bir raunt daha alırsak devreyi kazanırız. | 55 |
| casual | guys mute that guy, he is crying all game | arkadaşlar bu adamı susturuyor, bütün oyun boyunca ağlıyor. | Arkadaşlar şu adamı susturun, bütün oyun ağlıyor. | 71 |
| casual | can someone drop me AK please | Biri bana AK bırakabilir mi lütfen ? | Biri bana AK atabilir mi lütfen? | 80 |
