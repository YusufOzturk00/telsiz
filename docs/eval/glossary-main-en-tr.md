# Translation check: en -> tr (Argos, glossary on)

30 phrases, average 31 ms per phrase on CPU.
chrF compares characters with one reference translation (0-100, higher is closer);
it is a rough guide, read the translations themselves.

| Category | Phrases | chrF |
|---|---|---|
| clean | 10 | 58.4 |
| broken | 10 | 51.7 |
| slang | 7 | 67.7 |
| casual | 3 | 34.6 |
| **all** | 30 | **55.2** |

| Category | Source | Telsiz | Reference | chrF |
|---|---|---|---|---|
| clean | They're rushing B, five of them. | Rush atıyorlar B, beş tanesi. | B'ye rush atıyorlar, beşi birden. | 46 |
| clean | One is in A long, he has an AWP. | Biri A long'da, bir AWP var. | Biri A long'da, elinde AWP var. | 65 |
| clean | Save your weapon, we can't win this round. | Silahını kurtar, bu raundu kazanamayız. | Silahını kurtar, bu raundu kazanamayız. | 100 |
| clean | I'm low, one shot. | Canım az, tek mermilik. | Canım az, tek mermilik canım kaldı. | 65 |
| clean | Let's eco this round and full buy next. | Eco yapalım bu raunt ve full buy bir sonraki. | Bu raunt eco yapalım, sonrakinde full alalım. | 47 |
| clean | Smoke CT and flash for me. | Smoke CT ve flash benim için. | CT'ye smoke at, bana da flash at. | 21 |
| clean | The bomb is planted on A, go retake. | Bomba kuruldu A'da, retake'e gidin. | Bomba A'ya kuruldu, gidip geri alın. | 38 |
| clean | Watch mid, someone is lurking. | Mid'i izleyin, biri pusuda bekliyor. | Orta'ya dikkat et, biri pusuda bekliyor. | 57 |
| clean | Nice try, guys. We'll get the next one. | İyi denemeydi, arkadaşlar. Bir sonrakisini alacağız. | İyi denemeydi arkadaşlar. Sonrakini alırız. | 65 |
| clean | Don't peek, wait for the flash. | Kafa çıkarma, flash için bekleyin. | Kafa çıkarma, flash'ı bekle. | 72 |
| broken | he going B, I no have money | B'ye gidiyorum, param yok | B'ye gidiyor, param yok. | 79 |
| broken | why you not drop me weapon | Neden beni silahlamıyorsun | Neden bana silah atmıyorsun? | 51 |
| broken | they is three on A, careful | Onlar A'da üç, dikkatli | A'da üç kişiler, dikkat et. | 41 |
| broken | I am die, sorry, he was behind of box | Ben ölüyorum, üzgünüm, o kutunun arkasındaydı | Öldüm, kusura bakma, kutunun arkasındaydı. | 51 |
| broken | please you buy armor, not only gun | Lütfen zırh satın al, sadece silah değil | Lütfen zırh al, sadece silah değil. | 84 |
| broken | where is bomb? who have bomb? | Bomba nerede? Kim bombaladı? | Bomba nerede? Bomba kimde? | 56 |
| broken | me go A, you go B, okay? | A’ya gidiyorum, B’ye gider misin? | Ben A'ya gidiyorum, sen B'ye git, tamam mı? | 38 |
| broken | enemy very fast, he run to connector | Düşman çok hızlı, connector'a gidiyor | Düşman çok hızlı, connector'a koştu. | 80 |
| broken | stop shoot me, I am your team | Beni durdur, senin takımın | Bana ateş etmeyi kes, ben senin takımındanım. | 32 |
| broken | last round we lose because nobody defuse | Son raunt kaybediyoruz çünkü kimse defuse | Son raundu kimse bombayı imha etmediği için kaybettik. | 28 |
| slang | nt nt, ez next round | iyi denemeydi iyi denemeydi, bir sonraki raunt | İyi denemeydi, sonraki raunt kolay. | 63 |
| slang | gg wp, they're just better | iyi oyundu iyi oynadınız, onlar sadece daha iyi | İyi oyundu, onlar daha iyi. | 55 |
| slang | bro he's lit, like 20 hp | kanka adamın canı az, 20 can gibi | Kanka adamın canı az, 20 can falan. | 75 |
| slang | ninja defuse, go go go | ninja defuse, hadi hadi hadi | Gizlice imha et, hadi hadi hadi. | 46 |
| slang | he's baiting, don't swing | seni yemliyor, açılma | Seni yemliyor, açılma. | 89 |
| slang | rotate rotate, they faked A | dönün dönün, fake attılar A | Dönün dönün, A'ya fake attılar. | 67 |
| slang | my bad, I whiffed | benim hatam, ıskaladım | Benim hatam, ıskaladım. | 90 |
| casual | one more round and we win the half | Bir tane daha raunt ve yarıyı kazandık | Bir raunt daha alırsak devreyi kazanırız. | 29 |
| casual | guys mute that guy, he is crying all game | arkadaşlar o adamın hepsini ağlıyor | Arkadaşlar şu adamı susturun, bütün oyun ağlıyor. | 37 |
| casual | can someone drop me AK please | Birisi beni AK bırakabilir lütfen | Biri bana AK atabilir mi lütfen? | 39 |
