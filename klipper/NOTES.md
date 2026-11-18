# Ender 3 – optymalizacja (Klipper)

Notatki o stanie drukarki i pracy nad nią. Aktualizuj po każdej zmianie na drukarce.
Ostatnia aktualizacja: 2026-11-18 (sesja 16–18.11: akcelerometr MPU-6050, shapery X/Y, max_accel 2500, PA 0.11, kostki testowe).

## Stan na 13.11.2026 — skrót

Zrobione i zapisane w `printer.cfg` na Pi:
- `rotation_distance: 7.895` (skalibrowane, weryfikacja 100 mm OK)
- **`pressure_advance: 0.11`** (cofnięte z 0.175 dnia 16.11, wykonane i zweryfikowane: config i wartość na żywo 0.11). Powód: test linii #6 i macierz 6 kostek PA×przepływ — najlepsze kostki przy 0.11; wynik 0.175 ze słupka PA był odstający. Kopie: `printer-before-pa0175-20261116.cfg`, `printer-before-pa011b-20261116.cfg`. Uwaga: 16.11 wieczorem Mac nie rozwiązywał DNS `<pi-host>`; działało `ssh -o HostKeyAlias=<pi-host> <user>@<pi-ip>`. **Narożniki psują się powyżej ~3–4 mm niezależnie od PA (0.11–0.175), przepływu (90/100 %) i akceleracji (1500–3300) → przyczyna gdzie indziej**: podejrzewane: podwójne ściany w moich generatorach (nadmiar w narożnikach), wentylator 100 % / chłodzenie cienkiej ścianki, temperatura 210 °C. Test 16.11 wieczorem: `gcode/cubes4_walls_fan_temp.gcode` (4 kostki 25 mm, odstępy 75–85 mm po kolizjach głowicy z kostkami przy 35–45 mm; baza = 1 ściana/wentylator 100 %/210 °C; 2 = dwie ściany; 3 = wentylator 40 %; 4 = 195 °C).
- purge 2 × 200 mm w `START_PRINT`, z `M83` w `SAVE/RESTORE_GCODE_STATE`
- firmware płyty = host = v0.13.0-827
- wentylatory nazwane zgodnie z okablowaniem; płyta jako `[controller_fan]` 60 %
- czujniki temperatury MCU i Pi
- wyświetlacz ST7920 działa (taśma była odłączona)

Kopia aktualnych configów: `klipper-config-2026-11-18/` (starsza: `klipper-config-2026-11-13/`).

## TODO (kolejność proponowana)

0. **Wieża 20×20×20 (1 ściana, ustawienia z profilu Cury) wyszła kiepsko, 18.11** — dalsze strojenie w biurze wg planu w „Pressure advance — historia” (bisekcja po jednym parametrze od bazy 60 mm/s / ACCEL 500 / SCV 1 / 200 °C + prawdziwy model z Cury).
1. **Zwykły wydruk z ostrymi narożnikami** — kostki testowe 2 ściany OK (18.11, patrz „Pressure advance — historia”); zostaje prawdziwy model w sliceru z PA 0.11, ACCEL 2500, nową linią purge, temperaturą MCU/Pi i głośnością wentylatora płyty (z zamkniętą obudową).
2. **Stringing / retrakcja** (w toku od 18.11: dodane `[firmware_retraction]` 0.8 mm / 40 mm/s w `printer.cfg` (kopia przed: `printer-before-retraction-20261118.cfg`); wieża `gcode/retraction_tower_0.2-1.9.gcode` z `make_retraction_tower.py`: RETRACT_LENGTH = 0.2 + 0.06·(Z−1); **wynik 18.11: nitki znikają od Z=5 mm → 0.44 mm; ustawione `retract_length: 0.6`, `retract_speed 40`, `unretract_extra_length 0` w `printer.cfg`** (210 °C, PLA „raczej suchy”; kopia przed: `printer-before-retract06-20261118.cfg`); w sliceru ustawić retrakcję 0.6 mm / 40 mm/s albo G10/G11 (firmware retraction) — jeszcze do zrobienia). Pierwotnie odłożone 13.11: najpierw sprawdzić wilgotność filamentu (trzaski/bąbelki przy ekstruzji w powietrze; suszyć PLA 45–50 °C 4–6 h). Potem: włączyć `[firmware_retraction]`, slicer na G10/G11, wygenerować test 2 słupków z `TUNING_TOWER COMMAND=SET_RETRACTION PARAMETER=RETRACT_LENGTH` (~0.2→2.0 mm), ewentualnie test temperatury 190/195/200. Spodziewane ~0.5–1.0 mm dla direct Titan. Do ustalenia od użytkownika: filament, slicer, obecne ustawienia retrakcji.
3. **Rezonanse / input shaper**: sprawdzić mechanikę osi Y (kółka, ekscentryki, pasek, podłoże); RP2040 z MPU-6050 już działa (16.11) — ustalić `axes_map` wg montażu, potem `MEASURE_AXES_NOISE`, `SHAPER_CALIBRATE` X i Y. Obecny shaper 21/22.4 Hz jest oparty na wątpliwych danych.
4. Opcjonalnie: 3-przewodowy wentylator hotendu + tachometr + makro ochronne; radiator/wentylator na Pi, jeśli temperatura > ~70 °C.
5. Potwierdzić fizycznie typ hotendu (PTFE vs all-metal) — biała rurka PTFE wchodząca w radiator.

## Dostęp

- Pi: `<pi-host>` (hostname `<pi-hostname>`), SSH `<user>@…` kluczem (`-o BatchMode=yes`). **sudo dla `<user>` WYMAGA hasła** (`/etc/sudoers.d/010_pi-nopasswd` dotyczy tylko `pi`) — komendy z sudo uruchamia użytkownik.
- **Desktop z Curą: `<desktop>` (Linux/Ubuntu), login `<user>`, `ssh -o BatchMode=yes <user>@<desktop>`** (klucz z Maca skopiowany 18.11; krótka nazwa `<desktop>` jest w `known_hosts`, `<desktop-fqdn>` nie). Cura: `~/.local/share/cura/5.12/` (AppImage w `~/Downloads`, 5.14 pobrany 18.11). Ustawienia drukarki „Creality Ender-3 / Ender-3 v2” są w `user/*_user.inst.cfg` (maszyna i ekstruder), start/end G-code w `definition_changes/` (już `START_PRINT …` / `END_PRINT`). **18.11 wpisałem tuning** (lista w `cura-settings-2026-11-18.md`: warstwa 0.2, linia 0.44, 2 ściany, 15 %, 210/60 °C, prędkości 80/100/100/60/30/200, akceleracja 2500/2000, jerk off, retrakcja 0.6 mm/40 mm/s, wentylator 100 % od 0.6 mm, **podpory wyłączone**). Kopia przed zmianą: `~/.local/share/cura/5.12.bak-20261118` (przywrócenie: zamknąć Curę, skasować `5.12`, `mv 5.12.bak-20261118 5.12`). Domyślna retrakcja Cury była 6.5 mm/25 mm/s. Zmieniać pliki tylko przy zamkniętej Curze.
- Moonraker: przez SSH na `http://localhost:7125` (z zewnątrz web UI Mainsail jest za hasłem).
- Config na Pi: `~/printer_data/config/printer.cfg` (+ `mainsail.cfg`, `timelapse.cfg`, `moonraker.conf`, `crowsnest.conf`, `sonar.conf`), G-code: `~/printer_data/gcodes/`, log: `~/printer_data/logs/klippy.log`.
- Kopie zapasowe na Pi z 13.11: `printer-before-{pa,purge,rd,fans,tempsensors}-20261113.cfg`.
- Klipper: `~/klipper`, venv `~/klippy-env` (ma numpy, NIE ma matplotlib → `scripts/calibrate_shaper.py` nie działa; liczyć przez `klippy/extras/shaper_calibrate.py`, `find_best_shaper(cd, scv=5.0)`).
- Nigdy `SAVE_CONFIG`/`RESTART`/flashowania podczas druku — sprawdzaj `print_stats.state`.
- Po wyłączeniu/włączeniu drukarki (lub wpięciu kabla pod napięciem) Klipper jest w `shutdown` („Lost communication with MCU”) → `FIRMWARE_RESTART`.
- Zmiany w configu: edycja na Pi + `POST /printer/restart`. Wartości ekstrudera można testować na żywo (`SET_EXTRUDER_ROTATION_DISTANCE`, `SET_PRESSURE_ADVANCE`) bez restartu (restart wyłącza grzanie).

## Sprzęt

- **Ender 3 / Ender 3 Pro** (NIE V2 — mono LCD ST7920; `CE3E3V2_*` to tylko prefiks profilu Cura), stół magnetyczny bez klipsów.
- Płyta: **BTT SKR Mini E3 V3** (STM32G0B1, USB `usb-Klipper_stm32g0b1xx_1E003A001450415833323520-if00`), bootloader 8 KiB.
- Wyświetlacz: ST7920 na EXP1 — obraz, przycisk i pokrętło działają. Test: `M117 tekst`.
- Głowica: najpewniej przeniesiona z drukarki **ToAuto/Koonovo Pyramid A1.1** (użytkownik potwierdza; nazwa starego repo „HEPA1.1” = HotEnd Pyramid A1.1). Wg źródeł: **Titan direct drive** 3:1, dysza 0.4, max 250 °C (inne źródło 270 — trzymać 250). Typ hotendu nieznany, zakładać PTFE. **Test przepływu 16.11 (PLA, 210 °C, ekstruzja w powietrze, 50 mm/krok, F=Q/2.405×60):** nitka równa do 20 mm³/s (użytkownik: „w miarę OK”; pierwsze mm każdego kroku gorsze — narastanie ciśnienia), 14 i 18 czysto; 30 mm³/s wykonane (grzałka trzymała 210 °C, moc ~0.5 — prawie bez wzrostu), ale **nie zweryfikowane** czy ekstruder nie ślizga się (brak testu z markerem). Głowica jest mocniejsza niż standardowy Ender 3 (użytkownik: „nie standardowy”). Robocze zalecenie: przepływ ≤ ~15 mm³/s przy 210 °C (≈75 % sprawdzonych 20), więcej po podniesieniu temp. i teście z markerem.
- Ekstruder: `rotation_distance: 7.895` @ 16 µkroków (~405 kroków/mm, pasuje do klona Titan ~418 nominalnie), `run_current 0.65`. Stara 8.3989 (381 kroków/mm) była wartością nominalną przepisaną z Marlina, dawała 94 mm zamiast 100. Max extrude-only = 50 mm → test ekstruzji jako 2× `G1 E50 F60` (znacznik 120 mm od wejścia, ma zostać 20 mm).
- BLTouch: offset −37, +2; `z_offset = 1.814` (18.11: test pierwszej warstwy `gcode/firstlayer_test.gcode` — najlepsze pole 3 = +0.03 mm, 210 °C; zmiana z 1.844; kopia przed: `printer-before-zoffset-20261118.cfg`).
- Akcelerometr (16.11): **MPU-6050** (WHO_AM_I 0x68, NIE ADXL345) na **RP2040** `usb-Klipper_rp2040_C66018688F364921-if00` przez I2C0: SDA=GPIO0, SCL=GPIO1 (`i2c0a`), adres 0x68. Firmware RP2040 = v0.13.0-827 (przeflashowane 16.11, `make flash` wymaga sudo). Config w `printer.cfg`: `[mcu rpip]`, `[mpu9250]` (i2c_mcu: rpip, i2c_bus: i2c0a, `axes_map: y,x,z`), `[resonance_tester]` (115,115,20). `ACCELEROMETER_QUERY CHIP=mpu9250` działa. Czujnik przypięty klipsem do boku stołu (mierzy tylko oś **Y**; X wymaga przeniesienia na karetkę), płasko, Z do góry; test ruchem stołu: oś X czujnika = oś Y drukarki → `axes_map: y,x,z` potwierdzone. `MEASURE_AXES_NOISE` (16.11): 2.6 / 1.7 / 8.6 mm/s² (OK). Wcześniej BUS_TIMEOUT = problem okablowania/zasilania. Po `make flash` z konsoli RP2040 (skan I2C) potrzebny FIRMWARE_RESTART dwa razy ("oids already allocated").

## Wentylatory i temperatury (potwierdzone testem 13.11)

| Gniazdo | Pin | Co jest podłączone | Sekcja |
|---|---|---|---|
| FAN0 | PC6 | nadmuch na wydruk | `[fan]` |
| FAN1 | PC7 | wentylator płyty | `[controller_fan board_fan]` 60 %, idle_timeout 30, kick_start 0.5, heater extruder+bed, steppery XYZE |
| FAN2 | PB15 | radiator hotendu | `[heater_fan hotend_fan]` 100 % > 50 °C — **NIE zmniejszać** |

- Wcześniej nazwy były zamienione (BTT i stary Marlin zakładają FAN1 = hotend). Działało przypadkiem.
- `heater_fan` włącza się też przy każdym niezerowym targecie grzałki (ważne przy testach).
- Wentylatory 2-przewodowe → brak RPM. Tachometr wymagałby wentylatora 3-przewodowego + `tachometer_pin: ^PC2` (Z-STOP, jeśli wolne) lub `^PC15`.
- `[temperature_sensor mcu]` (temperature_mcu) i `[temperature_sensor raspberry_pi]` (temperature_host). Idle: MCU ~34 °C, Pi ~57 °C. `vcgencmd get_throttled` = 0x80000 → Pi kiedyś dobiło do miękkiego limitu temperatury.

## Config — pozostałe parametry

- Kinematyka: X `position_max 235`; Y `position_min -22`, `position_max 215`; Z `position_min -2`. `max_velocity 300`, `max_accel 2500` (podniesione z 1500 dnia 16.11 po shaperach X 3hump_ei 68.2 / Y mzv 43.8; limit z kalibracji X ~3100; niesprawdzone jeszcze na wydruku — kopia przed: `printer-before-accel-20261116.cfg`).
- Nozzle PID: Kp 15.067, Ki 0.913, Kd 62.152 (SAVE_CONFIG). Bed PID: Kp 54.027 Ki 0.770 Kd 948.182.
- Siatka `hot60` (60 °C, zakres ~0.285 mm), ładowana w `START_PRINT`. Śruby stołu wypoziomowane przy 60 °C.
- `START_PRINT`: M104 S150, M190 stół, G4 2 min heat-soak, G28, `BED_MESH_PROFILE LOAD="hot60"`, M109 dysza, purge: Y=5 X20→220 i Y=6.5 X220→20 (24 mm filamentu na przejście, F1000, Z0.3), wipe do X=12. Purge jeszcze niesprawdzony na prawdziwym wydruku. Jest też nieużywane makro `PURGE_LINE`.
- `END_PRINT` (18.11: retrakcja 3 mm i unoszenie Z jednocześnie `G1 E-3 Z2 F2400`, potem Z+8 — wcześniej retrakcja w miejscu zostawiała kropkę na końcu wydruku; kopia przed: `printer-before-endprint-20261118.cfg`) parkuje w X=10 Y=200.
- `[input_shaper]`: zv 21.0 / 22.4 Hz — patrz rezonanse.

## Pressure advance — historia

- 0.25 (stara wartość) → wieże (v1: optimum ≥ 0.10; v2: ~0.20, trudne do oceny przy ACCEL 500) → test linii przy −6 % ekstruzji: 0.11 → **po korekcie rotation_distance: linie #9–10 → 0.085**.
- **16.11.2026, powtórka przy realnych warunkach** (210 °C, 20→100 mm/s, ACCEL 2500, `pa_lines_0.06-0.22_210C_100mms.gcode`, PA 0.06 + 0.01·(nr−1)): wybrana **linia #6 → `pressure_advance: 0.11`** (zapisane w `printer.cfg`; kopia przed: `printer-before-pa011-20261116.cfg`). Powód: wieża akceleracji 1500–3300 dała zaokrąglone narożniki z nadmiarem filamentu wypływającym w górę (za niskie PA 0.085 przy 100 mm/s i ostrych kątach). Skrypt `make_pa_lines.py` ma teraz opcjonalne parametry NOZZLE_T SLOW FAST ACCEL i na końcu przywraca PA 0.11 (zmienić w skrypcie, jeśli PA w configu się zmieni).
- **Wniosek 16.11 (kostki 30×30×10, jedna ściana, PA 0.11, przepływ 100 %, wentylator 100 %, `gcode/cubes4_lastweek_30x10.gcode`)**: baza „jak w zeszłym tygodniu” (60 mm/s, ACCEL 500, SCV 1, 200 °C) = OK → kalibracja ekstruzji z 13.11 nie jest przyczyną. Pojedyncza zmiana psuje cienką ścianę stopniowo: 100 mm/s → jeden róg rozłazi się od połowy wysokości; ACCEL 2500 + SCV 5 → zafalowanie na 2/3 wysokości; 210 °C → to samo zafalowanie. Żadna nie tak źle jak wcześniejsze słupki. Kostka z **dwiema ścianami** przy najostrzejszych ustawieniach (100 mm/s, ACCEL 2500, SCV 5, 210 °C) wyszła „znośnie” (wcześniejsza macierz). Wniosek: pojedyncza ściana 0.44 mm to bardzo czuły obiekt testowy, nie reprezentuje zwykłych wydruków (≥2 ściany + wypełnienie); do oceny ustawień drukować prawdziwy model. Dla cienkich pojedynczych ścian (vase) zostać przy ~60 mm/s, ACCEL ~500–1000, SCV ≤ 1–3, ~200 °C.
- **Wynik końcowy 16–18.11 (kostki 30×30×20, 2 ściany + wypełnienie 15 %, 210 °C, PA 0.11, SCV 5, wentylator 100 %, `gcode/cubes2_2wall_infill.gcode`)**: kostka 2 (ściana zewnętrzna **100 mm/s, ACCEL 2500**) wygląda **lepiej** niż kostka 1 (60 mm/s, ACCEL 1500) → przy zwykłych ścianach agresywne ustawienia są dobre; problem narożników dotyczył tylko cienkiej pojedynczej ściany. Zostaje `max_accel 2500`, PA 0.11. Do sprawdzenia dalej: ACCEL ~3000 (limit X ~3100), prawdziwy model w sliceru (zewn. ściana 100 mm/s przy warstwie 0.2 = 8.8 mm³/s; przy 0.28 → 12.3 mm³/s, nadal < 15).
- **18.11 wieczorem — wieża 20×20×20, 1 ściana, ustawienia „domyślne z profilu Cury” (`gcode/tower_20_1wall.gcode` z `make_tower_20.py`: ściana 80 mm/s, ACCEL 2000, SCV 5, 210 °C, PA 0.11, wentylator 100 % od warstwy 4, retrakcja 0.6 między warstwami): wyszła „kiepsko”** (użytkownik; bez szczegółów), mimo że „na dawnych ustawieniach wieże były OK” (baza z 16.11: 60 mm/s, ACCEL 500, SCV 1, 200 °C). Pierwsza warstwa po `z_offset` 1.814 wygląda sensownie, kropka na końcu: użytkownik uznał za nieistotną. **Hipoteza**: to znów czułość pojedynczej ściany na prędkość/ACCEL/SCV/temperaturę (patrz wniosek z 16.11), a nie błąd kalibracji — ale niepotwierdzone na prawdziwym modelu z Cury (2 ściany). **Plan na wizytę w biurze (użytkownik wraca do drukarki za jakiś dzień)**: (1) wydrukować tę samą wieżę z bazą 60 mm/s / ACCEL 500 / SCV 1 / 200 °C i zmieniać po jednym parametrze (prędkość → ACCEL → SCV → temperatura → wentylator), żeby znaleźć winowajcę; (2) niezależnie wydrukować prawdziwy model z Cury (2 ściany, nowy profil) i ocenić narożniki; (3) jeśli pojedyncza ściana nadal zła przy łagodnych ustawieniach — rozważyć wentylator 40–60 %, cooling cienkich ścianek, `min_layer_time`, ewentualnie temperaturę 200–205 °C i sprawdzić `square_corner_velocity`; (4) zanotować opis wady (zaokrąglone narożniki / nadmiar w górę / falowanie), bo ten był w poprzednich testach rozróżnikiem PA vs mechaniki.
- **Test linii** jest czytelniejszy niż wieża: `python3 gcode/make_pa_lines.py OUT.gcode START STEP COUNT` (1 warstwa, 30 mm @20 → 100 mm @120 → 30 mm @20 mm/s, ACCEL 1500, linia #1 z przodu Y=40, co 6 mm, znacznik co 5. linię; PA = START + STEP × (nr − 1)).
- Dla TPU osobny test (PA dużo wyższe).

## Input shaper / rezonanse

- **16.11.2026 (wynik końcowy): po dociągnięciu paska Y i uwolnieniu go od tarcia pik Y = 41–43 Hz (3 powtórzenia, stabilny). Zastosowane w `printer.cfg`: `shaper_type_y: mzv`, `shaper_freq_y: 43.8` (0.6 % drgań, wygładzanie 0.106, max_accel do ~5700). X nadal `zv` 21.0 (niezmierzony — czujnik na karetkę). `max_accel` został podniesiony do 2500 (patrz „Config — pozostałe parametry”). Napięcie paska zmienia rezonans → po zmianie napięcia powtórzyć `SHAPER_CALIBRATE AXIS=Y`. Kopia przed zmianą: `printer-before-shaper-20261116.cfg`.** **Powtórka 18.11 (czujnik przykręcony na stole, `axes_map: y,x,z` — teraz tak w configu; szum 3.2/3.8/6.2):** pik Y 43.0 Hz (jak 16.11 10:46), 52.8 Hz (Z), 107.5 Hz; fit mzv 44.6 Hz (0.6 %) ≈ obecne 43.8 → pasek Y się nie rozluźnił, bez zmian w configu. Dla pomiaru X (czujnik na głowicy) przestawić `axes_map` na `y,-z,-x`.
- **16.11.2026, oś X** (czujnik przykręcony na głowicy, `axes_map: y,-z,-x` — dla czujnika na głowicy; dla stołu/Y wrócić do `y,x,z`): jeden pik **13.7 Hz, 100 % w X** (96 % energii w X), reszta <2 %. Każdy shaper zostawia ~36–38 % drgań → shaperem się nie naprawi (jak Y przed dociągnięciem paska: 15.6 Hz → po dociągnięciu 41–43 Hz). Nic nie zapisano; X nadal `zv` 21.0. Do zrobienia: dociągnąć pasek X, sprawdzić ekscentryki/kółka karetki X i sztywność mocowania czujnika, powtórzyć `SHAPER_CALIBRATE AXIS=X`. Kopia configu: `printer-before-axesmapX-20261116.cfg`.
- **16.11.2026, oś X po dociągnięciu paska X (wynik końcowy)**: piki 23.5 / 31.3 / 74.3 / 107.5 Hz (2 powtórzenia zgodne; wcześniej 13.7 Hz). Po jeszcze mocniejszym napięciu paska (11:28): piki 23.5 / 35.2 / 82.1 / 107.5 Hz (31→35 i 74→82 poszły w górę wraz z napięciem, 23.5 i 107.5 stoją → nie pasek). **Zastosowane w `printer.cfg` (16.11): `shaper_type_x: 3hump_ei`, `shaper_freq_x: 68.2`** (zalecenie Klippera; 5.0 % drgań, wygładzanie 0.194, max_accel do ~3100). Alternatywy: ei 34.0 Hz (6.4 %, accel ≤2100), mzv 25.4 Hz (7.4 %, ≤1800). **Powtórka 18.11 (czujnik na głowicy, `y,-z,-x`, szum 2.2/7.0/8.4)**: piki 23.5 (większy, 1.06e4) / 31.3 / 74.3 / 107.5 Hz — pasek wrócił do stanu sprzed dodatkowego naciągnięcia (31.3 i 74.3 zamiast 35.2 i 82.1), główny pik 23.5 Hz nietknięty; fit: 3hump_ei 67.2 Hz (5.9 %) ≈ obecne 68.2 → bez zmian w configu. Dalsze naciąganie ma malejący sens. Oś X nadal ma pik 23.5 Hz (nie od paska — sprawdzić kółka karetki, sztywność ramy/masę głowicy). Kopia przed zmianą: `printer-before-shaperX-20261116.cfg`. `axes_map` zostaje `y,-z,-x` (czujnik na głowicy); dla testu Y na stole wrócić do `y,x,z`.
- Wcześniejsze przebiegi tego dnia (pasek luźny): `SHAPER_CALIBRATE AXIS=Y` (MPU-6050 na RP2040, klips na stole, 1 kHz; NIE zapisano `SAVE_CONFIG`): główny pik Y **15.6 Hz** (99 % w Y, ~70 % energii 0–25 Hz) — zgodny z ~14 Hz ze skanów z 2025 (inny czujnik) → to realna cecha mechaniki stołu, nie artefakt czujnika. Drugi pik **48.8 Hz w Z** (stół podskakuje / klips). Każdy shaper zostawia ~22–30 % drgań; Klipper zaproponował 2hump_ei 40.4 Hz (dopasowany do łącznego widma z Z — nietrafiony); dopasowanie tylko do Y: najlepszy zv 21.0 Hz (≈ obecny config 21.0/22.4). Wniosek: shaperem się tego nie naprawi — poprawić mechanikę Y (napięcie paska, ekscentryki/kółka stołu, śruby karetki, sztywność mocowania czujnika), potem powtórzyć. X nie zmierzony (czujnik na karetkę).

- Dane: `resonance_data-2025-01-31/` (9 skanów Y z 31.01.2025, stary hotend; X brak).
- Pik Y ~14 Hz (za nisko; typowo 35–50 Hz), każdy shaper zostawia 40–50 % drgań, zv 21 Hz = minimum ZV → shaper głównie zaokrągla narożniki.
- Podejrzenia: luźny montaż czujnika przy pomiarze, luźne kółka/ekscentryki Y, pasek Y, podłoże.

## Firmware

- Host i MCU płyty: **v0.13.0-827-g29d4ec2d6** (MCU przeflashowane 13.11 przez użytkownika).
- Configi buildów: `firmware-configs/` (lokalnie) i `~/firmware-configs/` na Pi: `skr-mini-e3-v3.config` (STM32G0B1, 8 KiB bootloader, 8 MHz, USB PA11/PA12), `rp2040-2025-01.config`. `~/klipper/.config` to teraz SKR.
- Flash SKR (użytkownik, sudo): `sudo systemctl stop klipper && cd ~/klipper && make flash FLASH_DEVICE=/dev/serial/by-id/usb-Klipper_stm32g0b1xx_1E003A001450415833323520-if00; sudo systemctl start klipper`.

## Stary Marlin (github.com/bartoszbielawski/Ender3-SKRME3V3-HEPA1.1, I–II 2024)

- Ender-3 + SKR Mini E3 V3, BLTouch (offset −45, −7), `CR10_STOCKDISPLAY`, NeoPixel 8 LED, PSU control, termistory typ 1, `HEATER_0_MAXTEMP 275`, stock Bowden 93 kroków/mm, LIN_ADVANCE K=0, input shaping 40/40 Hz domyślne. ESP32-S2 z ESP3D jako WiFi.

## Pliki w tym folderze

- `klipper-config-2026-11-18/` — **aktualne** configi z Pi (18.11: PA 0.11, max_accel 2500, shapery X/Y, sekcje RP2040/MPU).
- `klipper-config-2026-11-13/` — configi z Pi (koniec 13.11).
- `klipper-config-2026-11-11/` — configi z 11.11 (przed zmianami).
- `firmware-configs/` — configi buildów firmware.
- `gcode/` — `make_pa_lines.py`, testy linii PA, wieże PA v1/v2.
- `resonance_data-2025-01-31/` — skany rezonansu Y.

## Historia

- 11.11.2026 (sesja „3D printer setup”): aktualizacja Klippera i systemu, SSH, hasło do web UI, porządki w configu, START/END_PRINT z purge i heat-soak, wymiary stołu, PID dyszy, poziomowanie, z_offset 1.844, siatka hot60, testy pierwszej warstwy, wieża PA v1.
- 13.11.2026: wieża PA v2, analiza starych danych rezonansu, flash firmware SKR do v0.13, testy linii PA, kalibracja ekstrudera (8.3989 → 7.895), PA 0.085, purge 200 mm, naprawa wyświetlacza (taśma), zamienione wentylatory poprawione, czujniki temperatury MCU/Pi, analiza starego repo Marlina i głowicy z Pyramid A1.1. Retrakcja odłożona.
