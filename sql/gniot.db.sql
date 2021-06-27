CREATE TABLE sample (id INT unsigned auto_increment primary key,
    date timestamp default current_timestamp,
    temperature int, humidity int, gniot_id int, ts INT);
