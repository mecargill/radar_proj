alpha = 1;
f_0 = 20;
n_s = 3000;


tt = linspace(0, 90, n_s)'; %chirps are 10

f_tx = abs(alpha * mod(tt, 10) .* (-1.^floor(tt/10)) + f_0);
dt = 90/n_s;
phi = zeros(n_s, 1);
sum = 0;

for i = 1:n_s
    phi(i, 1) = sum + f_tx(i, 1) * dt;
    sum = phi(i, 1);
end
phi_del = phi;
delay = (round(linspace(0, 550, n_s)))';

fit = -(alpha/2) * (delay*90/n_s).^2  + (f_0 + alpha*tt*90/n_s) .* (delay*90/n_s);

fit_line =  f_0 * (delay*90/n_s);

for i = 1:n_s
    if i+delay(i) > 0 && i + delay(i) < n_s
        phi_del(i+delay(i), 1) = phi(i);
        
    end
end
hold off
scatter(tt, phi, 1)
hold on
scatter(tt, phi_del, 1)
title("TX vs RX Phase with still target")
figure()
hold off
scatter(tt, phi-phi_del, 1)
hold on
scatter(tt, fit, 1)
scatter(tt, fit_line, 1)
title("IF Beat Phase with still target")
