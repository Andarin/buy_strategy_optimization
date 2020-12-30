# -*- coding: utf-8 -*-

'''
[Buy Strategy Optimization - How to maximize profit in buying in light of uncertainty]
Author: [andarin]  

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
for more details.

You should have received a copy of the GNU General Public License along with this 
program; if not, see <http://www.gnu.org/licenses/>.

'''

import random
import time
import warnings

# Values given
N = 1000
C_T = 500
C_S = 1
V_W = 50
V_L = 0

# Values searched
prior_triangle = [max(N*0.15-x,0) for x in range(N)]
W_DISTRIBUTION = {x: prior_triangle[x]/sum(prior_triangle) for x in range(N)}

# Technical params
PROBA_THRESHOLD = 0.00002
MC_REPETITIONS = 1000
PRINT_PROGRESS_EVERY_X_SEC = 10
BREAK_EXACT_METHOD_AFTER_X_SEC = 15
METASTATS_PRECISION = 4
NUMBER_RANDOM_DRAW_EXACT_METHOD = 5
random.seed(271)

# Framework definitions to run comparison of strategies
def calc_stats(obs):
    stat_dict = {}
    stat_dict["mean"] = sum([payout*proba for payout,proba in obs])
    stat_dict["proba_win"] = sum([proba for payout,proba in obs if payout>0])
    stat_dict["proba_loss"] = sum([proba for payout,proba in obs if payout<=0])
    if stat_dict["proba_win"] > 0:
        stat_dict["mean_win"] = sum([payout*proba for payout,proba in obs if payout>0])/sum([proba for payout,proba in obs if payout>0])
    else:
        stat_dict["mean_win"] = None

    if stat_dict["proba_loss"] > 0:
        stat_dict["mean_loss"] = sum([payout*proba for payout,proba in obs if payout<=0])/sum([proba for payout,proba in obs if payout<=0])
    else:
        stat_dict["mean_loss"] = None
    return stat_dict


def calc_metastats(payouts, w_distribution):
    stat_dict = {"mean": 0, "mean_win": 0, "mean_loss": 0, "proba_win": 0, "proba_loss": 0}
    for w, w_proba in w_distribution.items():
        stat_dict["mean"] += payouts[w]["stats"]["mean"]*w_proba
        stat_dict["proba_win"] += payouts[w]["stats"]["proba_win"]*w_proba
        if payouts[w]["stats"]["proba_win"] >0:
            stat_dict["mean_win"] += payouts[w]["stats"]["mean_win"]*payouts[w]["stats"]["proba_win"]*w_proba
        stat_dict["proba_loss"] += payouts[w]["stats"]["proba_loss"]*w_proba
        if payouts[w]["stats"]["proba_loss"] >0:
            stat_dict["mean_loss"] += payouts[w]["stats"]["mean_loss"]*payouts[w]["stats"]["proba_loss"]*w_proba
    
    stat_dict = {k: round(v, METASTATS_PRECISION) for k,v in stat_dict.items()}
    return stat_dict


def calc_payout(decision, hist_list, w):
    l = N-w
    if len(hist_list) == N:
        warnings.warn("Function never stopped, it bought the whole box as singles.")
        return w*V_W + l*V_L - len(hist_list)*C_S
    elif decision == "buy":
        return w*V_W + l*V_L - C_T - len(hist_list)*C_S
    elif decision == "refuse":
        return sum(hist_list)*V_W + (len(hist_list) - sum(hist_list))*V_L - len(hist_list)*C_S
    else:
        raise ValueError("Wrong return value from function ! Should be [buy, refuse, continue]")


def eval_mc(f, w):
    payout_list = []
    for i_rep in range(MC_REPETITIONS):
        hist_list = []
        while True:
            if "random_float" in f.__code__.co_varnames:
                decision = f(hist_list, random_float=random.uniform(0, 1))
            else:
                decision = f(hist_list)
            if decision == "continue" and len(hist_list) < N:
                hist_list += random.choices([1,0], cum_weights=[w-sum(hist_list), N-len(hist_list)])
                continue
            else:
                payout = calc_payout(decision, hist_list, w)
                payout_list += [(payout, 1/MC_REPETITIONS)]
                break
    return payout_list


def eval_exact(f, w, start_time):
    payout_list = []
    tree = [((),1)]
    while len(tree) > 0:
        if time.time() - start_time > BREAK_EXACT_METHOD_AFTER_X_SEC:
            raise TimeoutError

        hist_list, proba = tree.pop()
        n_tries = len(hist_list)

        if "random_float" in f.__code__.co_varnames:
            # Case if decision is partly random
            if proba > PROBA_THRESHOLD:
                proba /= NUMBER_RANDOM_DRAW_EXACT_METHOD
                decision_list = [f(hist_list, random_float=random.uniform(0, 1)) for random_int in range(NUMBER_RANDOM_DRAW_EXACT_METHOD)]
            else:
                decision_list = [f(hist_list, random_float=random.uniform(0, 1))]
        else:
            # Case if decision is deterministic
            decision_list = [f(hist_list)]

        for decision in decision_list:
            if decision == "continue" and n_tries < N:
                proba_win_marginal = (w-sum(hist_list))/(N-n_tries)
                proba_loss_marginal = 1 - proba_win_marginal

                if proba > PROBA_THRESHOLD:
                    if proba_win_marginal > 0:
                        tree.append((hist_list + (1,), proba*proba_win_marginal))
                    if proba_loss_marginal > 0:
                        tree.append((hist_list + (0,), proba*proba_loss_marginal))
                else:
                    # Case if probability gets too small to be relevant
                    # Number of leafs of tree must be kept reasonable -> stop in smallest branches
                    random_draw = random.choices([1,0], cum_weights=[proba_win_marginal, 1])[0]
                    tree.append((hist_list + (random_draw,), proba))

            else:
                payout = calc_payout(decision, hist_list, w)
                payout_list += [(payout, proba)]
                
        return payout_list


class Progress():
    def  __init__(self, w_distribution, print_progress_every_x_sec):
        self.start_time = time.time()
        self.current_time = self.start_time
        self.w_n = len(w_distribution)
        self.print_progress_every_x_sec = print_progress_every_x_sec
    
    def print(self, iw):
        if time.time() - self.current_time > self.print_progress_every_x_sec:
            self.current_time = time.time()
            remaining_est_time = (self.current_time-self.start_time)/iw*(self.w_n-iw)
            print("Est. time remaining: " + str(round(remaining_est_time)) + "s")

            
def eval_f_over_prior(f, w_distribution, method="exact"):
    payouts = {}
    progress = Progress(w_distribution, PRINT_PROGRESS_EVERY_X_SEC)
    
    if method == "exact":
        def eval_f(f, w): return eval_exact(f, w, progress.start_time)
    else:
        def eval_f(f, w): return eval_mc(f, w)
    
    for iw, w in enumerate(w_distribution):
        progress.print(iw)
        payouts[w] = {"obs": eval_f(f, w)}
        payouts[w]["stats"] = calc_stats(payouts[w]["obs"])

    payouts["stats"] = calc_metastats(payouts, w_distribution)
    return payouts


def run_competition(competition):
    results = {}
    for fname, f in competition.items():
        try:
            results[fname] = eval_f_over_prior(f, W_DISTRIBUTION, method="exact")
        except TimeoutError:
            warnings.warn("Function takes too long to be exactly evaluated; falling back to Monte Carlo.")
            results[fname] = eval_f_over_prior(f, W_DISTRIBUTION, method="mc")
            
    return results


def get_competition():
    import strategies
    return {fname: f for fname, f in strategies.__dict__.items() if callable(f)}
