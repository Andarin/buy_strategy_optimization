from lib import N, C_T, C_S, V_W, V_L, W_DISTRIBUTION

# Strategies to compare
def buy(hist_list):
    return("buy")


def buy_if_x_success(hist_list, x):
    if sum(hist_list) == x:
        return("buy")
    return("continue")


def buy_if_extrapolation_fix_sample_x_yields_positive_profit(hist_list, x):
    if len(hist_list) == x:
        if (sum(hist_list)*V_W + (len(hist_list)-sum(hist_list))*V_L)/x*N > C_T + len(hist_list)*C_S:
            return("buy")
        else:
            return("refuse")
    return("continue")


def buy_if_success_ratio_geq_x(hist_list, x):
    if len(hist_list) > 0 and sum(hist_list)/len(hist_list) >= x:
        return("buy")
    return("continue")


def buy_random(hist_list, random_float):
    if random_float <= 0.5:
        return("buy")
    return("continue")
    

def buy_refuse_random(hist_list, random_float):
    if random_float < 0.34:
        return("buy")
    elif random_float < 0.67:
        return("refuse")
    return("continue")


