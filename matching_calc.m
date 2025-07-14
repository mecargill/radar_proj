z_s = 50;
z_l = 96 + 21.79j;

target_s = 77.5 + 40i;
%target_l = 50; WRONG

function result = par(z1, z2)
    result = z1*z2/(z1 + z2);
end

function result = pi_net(z, z_c1, z_L, z_c2)
    %where c1 is closest to z, L is middle, and c2 is closest to where we're
    %looking from. 
    result = par(z, z_c1);
    result = result + z_L;
    result = par(result, z_c2);
end
function result = L_net(z, z_L, z_c)
    result = z + z_L;
    result = par(result, z_c);
end
function result = error(z, target)
    result = abs(target - z);
end

n=10000;
z_c1_arr = -1i.*linspace(210, 212, n);
z_c2_arr = [1];
z_L_arr = 1i.*linspace(48, 50, n);


i = 0;
min_error = 1000;
vals = [0, 0, 0];
for z_c1 = z_c1_arr
    for z_c2 = z_c2_arr
        for z_L = z_L_arr
            %err = error(pi_net(z_s, z_c1, z_L, z_c2), target_s);
            err = abs(L_net(z_s, z_L, z_c1) - target_s);
            if  err < min_error
                vals = [z_c1, z_L, z_c2];
                min_error = err;
            end
            i = i+1;
            if mod(i, 1000*n) == 0
                disp(100 * i/n^2 + "%")
            end
        end
    end
end

disp(vals)
disp(min_error)

