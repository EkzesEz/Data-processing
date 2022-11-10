import pandas as pd
import math


CONST_ATTACHMENT = 'application.xlsx'
CONST_SYS_ERR_PATH = 'systematic error.xlsx'

CONST_TABULAR_DATA = pd.read_excel(CONST_ATTACHMENT)
CONST_SYS_ERR_DATA = pd.read_excel(CONST_SYS_ERR_PATH)


def theta(unit, num, additional=False):
    errors = list()
    possible_units = ['A', 'V', 'F', 'OM']
    unit = unit.upper()
    if not (unit in possible_units):
        print('\n{} - unit is not allowed\n'.format(unit))
        return 0

    range_df = CONST_SYS_ERR_DATA['Range, {}'.format(unit)]
    range_df = range_df[range_df >= num]

    range_id = range_df.index.values[0]
    range_value = range_df.values[0]

    for i in range(1, 5):
        errors.append(CONST_SYS_ERR_DATA['{}{}'.format(unit, i)][range_id])

    main_err = (num * errors[0] + range_value * errors[1]) / 100
    additional_err = (num * errors[2] + range_value * errors[3]) / 100
    if not additional:
        additional_err = 0

    return [main_err, additional_err]


def theta_std_summary(theta_arr):
    result = 0
    for th in theta_arr:
        result += th ** 2
    result = math.sqrt(result / 3)
    return result


def theta_summary(theta_arr, probability):
    theta_std = theta_std_summary(theta_arr)
    k_theta = get_k_theta(len(theta_arr), probability)
    return theta_std * k_theta


def absolute_error(std_theta_summary, std_mean, k_theta, t_stud):
    th_sum = k_theta * std_theta_summary
    epsilon = t_stud * std_mean

    std_sum = math.sqrt(std_theta_summary ** 2 + std_mean ** 2)
    k_sum = (epsilon + th_sum) / (std_mean + std_theta_summary)
    delta = k_sum * std_sum

    return delta


def get_t(n, probability):
    if n > 1000000000:
        n = 1000
    if n < 4:
        n = 4

    n_t_df = CONST_TABULAR_DATA['n, t']
    n_t_id = n_t_df[n_t_df >= n].index
    t = CONST_TABULAR_DATA[probability][n_t_id].values[0]

    return t


def get_d(n, probability):
    if n > 51:
        n = 51

    n_d_df = CONST_TABULAR_DATA['n, d']
    n_d_id = n_d_df[n_d_df >= n].index

    d_min_prob = 'dmin, {}'.format(probability)
    d_max_prob = 'dmax, {}'.format(probability)
    d_min = CONST_TABULAR_DATA[d_min_prob][n_d_id].values[0]
    d_max = CONST_TABULAR_DATA[d_max_prob][n_d_id].values[0]

    return [d_min, d_max]


def get_z(n, probability):
    if n > 49:
        n = 49

    n_z_df = CONST_TABULAR_DATA['n, z']
    n_z_id = n_z_df[n_z_df >= n].index

    z_prob = 'z, {}'.format(probability)
    z = CONST_TABULAR_DATA[z_prob][n_z_id].values[0]
    m = CONST_TABULAR_DATA['m'][n_z_id].values[0]

    return [z, m]


def get_k_theta(m, probability):
    if m > 5:
        m = 5

    m_k_df = CONST_TABULAR_DATA['m, k']
    m_k_id = m_k_df[m_k_df >= m].index

    k_prob = 'k, {}'.format(probability)
    k = CONST_TABULAR_DATA[k_prob][m_k_id].values[0]

    return k


# датафрейм вида |Xi - А|
def abs_diff(data, n):
    return data.apply(lambda x: abs(x - n))


def d(df):
    mean = df.mean()
    std1 = df.std(ddof=0)
    mean_diff_sum = abs_diff(df, mean).sum()
    d_ = mean_diff_sum/(df.size * std1)
    return d_


def is_gauss(data, d_min, d_max, z, m):
    d_ = d(data)
    if (d_ > d_max) | (d_ < d_min):
        print("\n| d-test is not passed:\n| {} < {} < {}".format(d_min, d_, d_max))
        print('\n|', data, '\n')
        return False

    # how many |Xi - X.mean()| > z * X.std()
    abs_diff_mean = abs_diff(data, data.mean())
    std = data.std()

    diff_counter = abs_diff_mean[abs_diff_mean > z * std].count()
    if diff_counter >= m:
        print('\n| m-test is not passed\n| {} > {}'.format(diff_counter, m))
        print('\n|', data, '\n')
        return False
    return True


# удаляет промахи по 3-сигма алгоритму. Возвращает массив ошибок
def delete_miss(df):
    misses = []
    while 1:
        abs_diff_df = abs_diff(df, df.mean())
        miss_id = abs_diff_df[abs_diff_df == abs_diff_df.max()].index

        # грубо говоря, проверка на то, является ли распределение равномерным
        if miss_id.size == df.count():
            break

        max_diff_element = df[miss_id].values[0]
        new_df = df.drop(miss_id)
        mean_new = new_df.mean()
        std_new = new_df.std()

        if abs(max_diff_element - mean_new) <= 3 * std_new:
            break
        df = new_df
        misses += max_diff_element

    if len(misses) > 0:
        print('| All misses:', misses)
    return misses
