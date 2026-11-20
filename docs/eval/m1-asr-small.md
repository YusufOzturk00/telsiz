# Speech recognition check: Whisper small on cuda

| Clip | Condition | Prompt | Detected | WER | Time | Transcript |
|---|---|---|---|---|---|---|
| en_magi_1.wav | clean | yes | en 1.00 | 0% | 1015 ms | One dollar and eighty-seven cents, that was all. And sixty cents of it was in pennies. |
| en_magi_1.wav | clean | no | en 1.00 | 6% | 771 ms | $1.87. That was all. And 60 cents of it was in pennies. |
| en_magi_1.wav | voice chat | yes | en 1.00 | 0% | 724 ms | One dollar and 87 cents. That was all. And 60 cents of it was in pennies. |
| en_magi_1.wav | voice chat | no | en 1.00 | 12% | 679 ms | One dollar and eighty-seven cents. That was all. Sixty cents if it was in pennies. |
| en_magi_1.wav | bad voice chat | yes | en 1.00 | 12% | 659 ms | One dollar and 87 cents. That was all. 60 cents of it was in penny. |
| en_magi_1.wav | bad voice chat | no | en 1.00 | 12% | 670 ms | One dollar and eighty-seven cents. That was all. Sixty cents of it was in penny. |
| en_magi_2.wav | clean | yes | en 1.00 | 18% | 633 ms | 3 times Del accounted it, $1.87, and the next day would be Christmas. |
| en_magi_2.wav | clean | no | en 1.00 | 18% | 579 ms | Three times Del accounted it, $1.87 and the next day would be Christmas. |
| en_magi_2.wav | voice chat | yes | en 1.00 | 18% | 636 ms | Three times Del accounted it, $1.87, and the next day would be Christmas. |
| en_magi_2.wav | voice chat | no | en 1.00 | 12% | 590 ms | Three times double counted it, $1.87 and the next day would be Christmas. |
| en_magi_2.wav | bad voice chat | yes | en 0.99 | 29% | 639 ms | Three times they'll accounted it, $1.87, and the next day will be Christmas. |
| en_magi_2.wav | bad voice chat | no | en 0.99 | 24% | 604 ms | Three times that was counted as $1.87 and the next day would be Christmas. |
| ru_belkin_1.wav | clean | yes | ru 1.00 | 7% | 1530 ms | Для сего обратились было мы к Марии Алексеевной Трофилиной, ближайшей родственнице и наследнице Ивана Петровича Белкина. Но, к сожалению, ей невозможно было нам доставить никакого о нем известия. |
| ru_belkin_1.wav | voice chat | yes | ru 0.99 | 29% | 1609 ms | Для него обратились головы к Марии Алексеевной Трофимовой, ближайшей родственницей и наследницей Иваны Петровича Белкина. Но, к сожалению, ей невозможно было нам доставить никакого о нем известия. |
| ru_belkin_1.wav | bad voice chat | yes | ru 0.97 | 61% | 1788 ms | Спасибо, обратились в голову к варии Алексея Митрофимеевича. Ближайшие родственники, яблоки и Иваны Петровича Березина. Но, к сожалению, мне невозможно было нам доставить никакого момента действия. |
| ru_belkin_2.wav | clean | yes | ru 1.00 | 7% | 1098 ms | Она советовала нам отнестись по всему предмету к одному почтенному мужу, бывшему другом Ивану Петровичу. |
| ru_belkin_2.wav | voice chat | yes | ru 1.00 | 33% | 1067 ms | Она советовала нам отнести всему предмету к одному почтенному мужу, бывшему другу Ивана Петровичу. |
| ru_belkin_2.wav | bad voice chat | yes | ru 0.99 | 93% | 1080 ms | Она советовала нам отнести всему привету к одному почти одну минуту. С лучшему другу мы вам дикую вечеру. |
