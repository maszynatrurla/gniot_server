CREATE TABLE pogoda (id INT unsigned auto_increment primary key, date timestamp default current_timestamp,
    temperature_bmp real, pressure real, temperature_dht real, humidity real, solar_mv int, smog_pm1_0_cf1 int,
    smog_pm2_5_cf1 int, smog_pm10_cf1 int, smog_pm1_0 int, smog_pm2_5 int, smog_pm10 int, smog_part0_3 int,
    smog_part0_5 int, smog_part1_0 int, smog_part2_5 int, smog_part5_0 int, smog_part10 int);
