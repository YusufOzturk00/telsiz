# Translation check: en -> tr (nllb-1.3b, glossary off)

30 phrases, average 645 ms per phrase on CPU (4 threads).
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 10 | 39.2 |
| broken | 10 | 52.0 |
| slang | 7 | 25.1 |
| casual | 3 | 63.8 |
| **all** | 30 | **43.9** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | They're rushing B, five of them. | B'ye koşuşuyorlar, beş kişi. | B'ye rush atıyorlar, beşi birden. | 38 |
| clean | One is in A long, he has an AWP. | Bir tanesi A uzunluğunda, AWP var. | Biri A long'da, elinde AWP var. | 31 |
| clean | Save your weapon, we can't win this round. | Silahını sakla, bu raundu kazanamayız. | Silahını kurtar, bu raundu kazanamayız. | 75 |
| clean | I'm low, one shot. | Düşük, tek atış. | Canım az, tek mermilik canım kaldı. | 10 |
| clean | Let's eco this round and full buy next. | Bu turda ekol yapalım ve bir dahaki turda tam alım yapalım. | Bu raunt eco yapalım, sonrakinde full alalım. | 28 |
| clean | Smoke CT and flash for me. | Benim için tomografi ve flaş yap. | CT'ye smoke at, bana da flash at. | 11 |
| clean | The bomb is planted on A, go retake. | Bomba A'ya yerleştirildi, geri alın. | Bomba A'ya kuruldu, gidip geri alın. | 50 |
| clean | Watch mid, someone is lurking. | Dikkat et, biri pusuya yatıyor. | Orta'ya dikkat et, biri pusuda bekliyor. | 51 |
| clean | Nice try, guys. We'll get the next one. | İyi deneme, çocuklar. Bir sonrakini alacağız. | İyi denemeydi arkadaşlar. Sonrakini alırız. | 47 |
| clean | Don't peek, wait for the flash. | Bakma, flaşı bekle. | Kafa çıkarma, flash'ı bekle. | 39 |
| broken | he going B, I no have money | B, param yok. | B'ye gidiyor, param yok. | 46 |
| broken | why you not drop me weapon | Neden silahımı bırakmıyorsun ? | Neden bana silah atmıyorsun? | 50 |
| broken | they is three on A, careful | A'da üç. Dikkatli olun. | A'da üç kişiler, dikkat et. | 31 |
| broken | I am die, sorry, he was behind of box | Öldüm, üzgünüm, kutu arkasındaydı. | Öldüm, kusura bakma, kutunun arkasındaydı. | 51 |
| broken | please you buy armor, not only gun | Lütfen zırh al, sadece silah değil. | Lütfen zırh al, sadece silah değil. | 100 |
| broken | where is bomb? who have bomb? | Bomba nerede? Kimde bomba var? | Bomba nerede? Bomba kimde? | 60 |
| broken | me go A, you go B, okay? | Ben A, sen B, tamam mı? | Ben A'ya gidiyorum, sen B'ye git, tamam mı? | 35 |
| broken | enemy very fast, he run to connector | Düşman çok hızlı, bağlantıya koştu. | Düşman çok hızlı, connector'a koştu. | 59 |
| broken | stop shoot me, I am your team | Beni vurmayı kes, ben senin takımınım. | Bana ateş etmeyi kes, ben senin takımındanım. | 54 |
| broken | last round we lose because nobody defuse | Son rauntta kaybettik çünkü kimse etkisiz hale getirmedi . | Son raundu kimse bombayı imha etmediği için kaybettik. | 38 |
| slang | nt nt, ez next round | Bir sonraki turda. | İyi denemeydi, sonraki raunt kolay. | 22 |
| slang | gg wp, they're just better | GG WP, daha iyiler. | İyi oyundu, onlar daha iyi. | 26 |
| slang | bro he's lit, like 20 hp | Dostum yanıyor, 20 beygir gibi. | Kanka adamın canı az, 20 can falan. | 8 |
| slang | ninja defuse, go go go | Ninja etkisizleştir, git git git | Gizlice imha et, hadi hadi hadi. | 12 |
| slang | he's baiting, don't swing | O yem yapıyor, sallama. | Seni yemliyor, açılma. | 22 |
| slang | rotate rotate, they faked A | Döner döner, A'yı sahte yaptılar. | Dönün dönün, A'ya fake attılar. | 31 |
| slang | my bad, I whiffed | Benim hatam, kokladım. | Benim hatam, ıskaladım. | 65 |
| casual | one more round and we win the half | Bir tur daha ve yarısını kazanırız . | Bir raunt daha alırsak devreyi kazanırız. | 37 |
| casual | guys mute that guy, he is crying all game | Çocuklar şu adamı susturun, bütün oyun boyunca ağlıyor. | Arkadaşlar şu adamı susturun, bütün oyun ağlıyor. | 75 |
| casual | can someone drop me AK please | Biri bana AK bırakabilir mi lütfen ? | Biri bana AK atabilir mi lütfen? | 80 |
