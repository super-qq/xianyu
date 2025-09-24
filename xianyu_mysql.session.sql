select * from product;

select * from pre_product;


desc product;

INSERT INTO xianyu.pre_product (
  summary, 
  tao_token, 
  price, 
  product_id, 
  is_release
) VALUES ('浪莎半高领德绒女士打底衫 黑 白2件🧥 加绒保暖，内搭外穿
',
  'https://u.jd.com/POTF1h8', 
  60.3,
  NULL,
  0
);

desc pre_product;


update pre_product set is_release = 0 WHERE id = 2;