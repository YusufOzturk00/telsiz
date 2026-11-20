# Speech recognition check: Whisper large-v3-turbo on cuda

| Clip | Condition | Prompt | Detected | WER | Time | Transcript |
|---|---|---|---|---|---|---|
| en_magi_1.wav | clean | yes | en 1.00 | 0% | 2175 ms | One dollar and eighty-seven cents. That was all. And sixty cents of it was in pennies. |
| en_magi_1.wav | clean | no | en 1.00 | 0% | 11955 ms | one dollar and eighty-seven cents that was all and sixty cents of it was in pennies |
| en_magi_1.wav | voice chat | yes | en 1.00 | 6% | 44438 ms | One dollar and eighty-seven cents. That was all. Sixty cents of it was in pennies. |
| en_magi_1.wav | voice chat | no | en 1.00 | 6% | 14875 ms | One dollar and eighty-seven cents. That was all. Sixty cents of it was in pennies. |
| en_magi_1.wav | bad voice chat | yes | en 1.00 | 19% | 492 ms | $1.87. That was all. $0.60 of it was in pennies. |
| en_magi_1.wav | bad voice chat | no | en 1.00 | 19% | 480 ms | $1.87. That was all. $0.60 of it was in pennies. |
| en_magi_2.wav | clean | yes | en 1.00 | 6% | 485 ms | Three times Della counted it, $1.87, and the next day would be Christmas. |
| en_magi_2.wav | clean | no | en 1.00 | 6% | 475 ms | Three times Della counted it, $1.87, and the next day would be Christmas. |
| en_magi_2.wav | voice chat | yes | en 1.00 | 6% | 476 ms | Three times Della counted it, $1.87, and the next day would be Christmas. |
| en_magi_2.wav | voice chat | no | en 1.00 | 6% | 480 ms | Three times Della counted it, $1.87, and the next day would be Christmas. |
| en_magi_2.wav | bad voice chat | yes | en 1.00 | 12% | 473 ms | Three times Bella counted it, $1.87. And the next day would be Christmas. |
| en_magi_2.wav | bad voice chat | no | en 1.00 | 12% | 472 ms | Three times Bella counted it, $1.87, and the next day would be Christmas. |
| ru_belkin_1.wav | clean | yes | ru 1.00 | 4% | 1078 ms | Для сего обратились было мы к Марии Алексеевне Трофилиной, ближайшей родственнице и наследнице Ивана Петровича Белкина. Но, к сожалению, ей невозможно было нам доставить никакого о нем известия. |
| ru_belkin_1.wav | voice chat | yes | ru 1.00 | 4% | 12718 ms | Для сего обратились было мы к Марии Алексеевне Трофилиной, ближайшей родственнице и наследнице Ивана Петровича Белкина. Но, к сожалению, ей невозможно было нам доставить никакого о нем известия. |
| ru_belkin_1.wav | bad voice chat | yes | ru 1.00 | 21% | 577 ms | Для всего обратились мы к Марии Алексеевне Трофимовне, ближайшей родственнице Ивана Петровича Делкина. Но, к сожалению, ей невозможно было нам доставить никакого о нем известия. |
| ru_belkin_2.wav | clean | yes | ru 1.00 | 7% | 514 ms | Она советовала нам отнестись по всему предмету к одному почтенному мужу, бывшему другом Ивану Петровичу. |
| ru_belkin_2.wav | voice chat | yes | ru 1.00 | 7% | 514 ms | Она советовала нам отнестись по всему предмету к одному почтенному мужу, бывшему другом Ивану Петровичу. |
| ru_belkin_2.wav | bad voice chat | yes | ru 1.00 | 27% | 516 ms | Она советовала нам отнести всему предмету к одному почтенному мужу, бывшему другу Ивану Петровичу. |
