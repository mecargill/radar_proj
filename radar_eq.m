c = 299792458; %m/s
f = 2.45 * 10^9;%Hz
lam = c/f;
G_db = 6;
G = 10^(G_db/10);
R = [1 5 10 15];%m
RCA = [1 10 40];%m^2
P_dbms = [21 24.5 27 30];

temp = 10^(21/10);

disp(10*log10((temp * G^2 * lam^2)/(64 * pi^3)))
for P_dbm = P_dbms
    disp("Conducted Power Level (dBm) " + P_dbm)
    P = 10^(P_dbm/10);%mW

    disp(10*log10((P * lam^2 * G^2 * (4*pi)^-3) * (R.^-4)' * (RCA)))
end
