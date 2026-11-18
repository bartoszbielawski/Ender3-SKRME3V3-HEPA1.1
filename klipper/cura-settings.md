# Ustawienia Cury pod tuning Klippera (18.11.2026)

Opierają się na testach z 16–18.11: PA 0.11, `max_accel` 2500, shapery X `3hump_ei` 68.2 Hz / Y `mzv` 43.8 Hz,
retrakcja 0.6 mm / 40 mm/s (wieża retrakcji: nitki znikają od 0.44 mm), PLA 205–210 °C, stół 60 °C.
Nie ma tu nic o PA ani shaperach — to ustawia Klipper, nie slicer.

## Maszyna → G-code

- **Start G-code** (jedna linia; makro robi nagrzanie stołu, heat-soak 2 min, G28, siatkę `hot60`, nagrzanie dyszy i purge):

      START_PRINT BED_TEMP={material_bed_temperature_layer_0} EXTRUDER_TEMP={material_print_temperature_layer_0}

- **End G-code** (makro: retrakcja 3 mm, Z+10, parkowanie X10 Y200, wyłączenie grzania i wentylatora):

      END_PRINT

- Rozmiar stołu 235 × 215 (Y ma `position_max 215`), dysza 0.4, średnica filamentu 1.75.
- Wydruk **nie** wymaga `G28` ani innego homingu w sliceru — robi to `START_PRINT`.

## Materiał (PLA)

| Ustawienie | Wartość |
|---|---|
| Temperatura druku | 205–210 °C (zacznij od 210; 200 °C też działało na cienkiej ścianie) |
| Temperatura pierwszej warstwy | 210 °C |
| Temperatura stołu / pierwszej warstwy | 60 °C (siatka `hot60` jest zmierzona przy 60 °C) |
| Przepływ | 100 % (po kalibracji `rotation_distance` 7.895) |

## Jakość

| Ustawienie | Wartość |
|---|---|
| Wysokość warstwy | 0.2 mm (0.28 dla szkiców) |
| Szerokość linii | 0.44 mm (pierwsza warstwa: 110 %) |
| Liczba ścian | 2 (3 dla elementów wytrzymałościowych) |
| Wypełnienie | 10–15 %, wzór grid lub trójkąty |

## Prędkość (limit przepływu: ≤ 15 mm³/s = prędkość × wysokość × szerokość linii)

| Ustawienie | Wartość |
|---|---|
| Ściana zewnętrzna | 80–100 mm/s (kostki z 2 ścianami przy 100 mm/s, akceleracja 2500 wyszły najlepiej) |
| Ściana wewnętrzna | 100 mm/s |
| Wypełnienie | 100 mm/s |
| Góra/dół | 60 mm/s |
| Pierwsza warstwa | 30 mm/s |
| Przejazdy | 200 mm/s (Klipper obcina do `max_velocity` 300) |

Przy warstwie 0.28 i linii 0.44 100 mm/s daje 12.3 mm³/s, nadal poniżej 15.

## Akceleracja (włącz „Kontrola przyspieszenia")

| Ustawienie | Wartość |
|---|---|
| Przyspieszenie druku | 2500 (nie więcej: `max_accel` w configu = 2500, limit osi X ≈ 3100) |
| Ściana zewnętrzna | 1500–2500 |
| Przejazdy | 2500 |
| Kontrola szarpnięcia (jerk) | **wyłączona** (Klipper używa `square_corner_velocity` 5 mm/s, nie obsługuje M205) |

## Retrakcja

| Ustawienie | Wartość |
|---|---|
| Włącz retrakcję | tak |
| Odległość retrakcji | 0.6 mm |
| Prędkość retrakcji | 40 mm/s |
| Minimalny przejazd przed retrakcją | 1.5 mm |
| Z-hop | wyłączony |
| Combing | w wypełnieniu (nie „wszędzie") |

Cura wysyła zwykłe `G1 E-0.6`; Klipper to wykona. Jeśli używasz wtyczki „Firmware Retraction"
(G10/G11), nie włączaj jednocześnie zwykłej retrakcji — wartości z `[firmware_retraction]` w configu
(0.6 mm / 40 mm/s) mają wtedy pierwszeństwo.

## Chłodzenie

| Ustawienie | Wartość |
|---|---|
| Wentylator | 100 % od warstwy 4 (0.6 mm), 0 % na pierwszych warstwach |
| Minimalny czas warstwy | 5–10 s dla małych elementów (cienkie ścianki przegrzewają się przy krótkim czasie warstwy) |

## Przyczepność

- Brim lub skirt 1–2 linie (purge z `START_PRINT` jest przy Y = 5–6.5, nie koliduje).
- Stół magnetyczny bez klipsów — przy wysokich cienkich modelach brim 5 mm.

## Inne

- **Ekstruzja względna** („Use relative extrusion"): włącz (Klipper działa poprawnie w obu trybach).
- **Plik wyjściowy**: G-code (Klipper), wgraj przez Mainsail.
- Przed wydrukiem upewnij się, że czujnik MPU-6050 jest zdjęty z głowicy lub stołu.
