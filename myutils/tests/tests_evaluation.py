from django.test import TestCase

from myutils.evaluation import (
    dcg_at_k,
    evaluate_recommendations,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    train_test_split,
)


class TrainTestSplitTests(TestCase):
    def test_split_ratio(self):
        ratings = [(i, i + 100, float(i % 10)) for i in range(100)]
        train, test = train_test_split(ratings, ratio=0.8, seed=42)
        self.assertEqual(len(train), 80)
        self.assertEqual(len(test), 20)

    def test_no_data_leakage(self):
        ratings = [(i, i + 100, float(i % 10)) for i in range(50)]
        train, test = train_test_split(ratings, ratio=0.8, seed=42)
        train_set = set(train)
        test_set = set(test)
        self.assertEqual(len(train_set & test_set), 0)

    def test_deterministic_with_seed(self):
        ratings = [(i, i, float(i)) for i in range(20)]
        train1, test1 = train_test_split(ratings, ratio=0.7, seed=123)
        train2, test2 = train_test_split(ratings, ratio=0.7, seed=123)
        self.assertEqual(train1, train2)
        self.assertEqual(test1, test2)

    def test_empty_input(self):
        train, test = train_test_split([], ratio=0.8)
        self.assertEqual(train, [])
        self.assertEqual(test, [])


class PrecisionAtKTests(TestCase):
    def test_perfect_precision(self):
        recommended = [1, 2, 3, 4, 5]
        relevant = {1, 2, 3, 4, 5}
        self.assertAlmostEqual(precision_at_k(recommended, relevant, 5), 1.0)

    def test_zero_precision(self):
        recommended = [6, 7, 8, 9, 10]
        relevant = {1, 2, 3, 4, 5}
        self.assertAlmostEqual(precision_at_k(recommended, relevant, 5), 0.0)

    def test_partial_precision(self):
        recommended = [1, 6, 2, 7, 3]
        relevant = {1, 2, 3}
        self.assertAlmostEqual(precision_at_k(recommended, relevant, 5), 0.6)

    def test_k_zero(self):
        self.assertAlmostEqual(precision_at_k([1, 2], {1}, 0), 0.0)

    def test_k_larger_than_list(self):
        recommended = [1, 2]
        relevant = {1, 2, 3}
        self.assertAlmostEqual(precision_at_k(recommended, relevant, 5), 1.0)


class RecallAtKTests(TestCase):
    def test_perfect_recall(self):
        recommended = [1, 2, 3]
        relevant = {1, 2, 3}
        self.assertAlmostEqual(recall_at_k(recommended, relevant, 3), 1.0)

    def test_zero_recall(self):
        recommended = [4, 5, 6]
        relevant = {1, 2, 3}
        self.assertAlmostEqual(recall_at_k(recommended, relevant, 3), 0.0)

    def test_partial_recall(self):
        recommended = [1, 4, 5]
        relevant = {1, 2, 3}
        self.assertAlmostEqual(recall_at_k(recommended, relevant, 3), 1 / 3)

    def test_empty_relevant(self):
        self.assertAlmostEqual(recall_at_k([1, 2], set(), 2), 0.0)


class NDCGAtKTests(TestCase):
    def test_perfect_ordering(self):
        recommended = [1, 2, 3]
        relevant = {1, 2, 3}
        self.assertAlmostEqual(ndcg_at_k(recommended, relevant, 3), 1.0)

    def test_worst_case(self):
        recommended = [4, 5, 6]
        relevant = {1, 2, 3}
        self.assertAlmostEqual(ndcg_at_k(recommended, relevant, 3), 0.0)

    def test_partial_ordering(self):
        # Only first item is relevant — NDCG should be > 0 but < 1
        recommended = [1, 4, 5]
        relevant = {1, 2, 3}
        score = ndcg_at_k(recommended, relevant, 3)
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_k_zero(self):
        self.assertAlmostEqual(ndcg_at_k([1], {1}, 0), 0.0)


class EvaluateRecommendationsTests(TestCase):
    def test_aggregation(self):
        user_recs = {
            "u1": [1, 2, 3, 4, 5],
            "u2": [1, 6, 7, 8, 9],
        }
        user_rel = {
            "u1": {1, 2, 3},
            "u2": {1, 2},
        }
        metrics = evaluate_recommendations(user_recs, user_rel, k=5)
        self.assertIn("precision_at_k", metrics)
        self.assertIn("recall_at_k", metrics)
        self.assertIn("ndcg_at_k", metrics)
        self.assertGreater(metrics["precision_at_k"], 0.0)

    def test_no_users(self):
        metrics = evaluate_recommendations({}, {}, k=5)
        self.assertEqual(metrics["precision_at_k"], 0.0)
