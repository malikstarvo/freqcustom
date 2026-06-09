import logging
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
from pandas import DataFrame
from pandas.api.types import is_integer_dtype
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from freqtrade.freqai.base_models.BaseClassifierModel import BaseClassifierModel
from freqtrade.freqai.data_kitchen import FreqaiDataKitchen

logger = logging.getLogger(__name__)


class XGBoostGridSearchModel(BaseClassifierModel):

    def fit(self, data_dictionary: dict, dk: FreqaiDataKitchen, **kwargs) -> Any:
        X = data_dictionary["train_features"].to_numpy()
        y = data_dictionary["train_labels"].to_numpy()[:, 0]

        le = LabelEncoder()
        if not is_integer_dtype(y):
            y = pd.Series(le.fit_transform(y), dtype="int64")

        test_size = self.freqai_info.get("data_split_parameters", {}).get("test_size", 0.1)
        if test_size == 0:
            eval_set = None
            eval_metric = None
        else:
            test_features = data_dictionary["test_features"].to_numpy()
            test_labels = data_dictionary["test_labels"].to_numpy()[:, 0]

            if not is_integer_dtype(test_labels):
                test_labels = pd.Series(le.transform(test_labels), dtype="int64")

            eval_set = [(test_features, test_labels)]
            eval_metric = "auc"

        train_weights = data_dictionary["train_weights"]

        gs_params = self.freqai_info.get("grid_search_parameters", {})
        if not gs_params:
            gs_params = {
                "max_depth": [3, 5],
                "learning_rate": [0.03, 0.05, 0.1],
                "n_estimators": [200, 500],
                "subsample": [0.8, 1.0],
                "colsample_bytree": [0.8, 1.0],
            }

        fit_params = {}
        if eval_set is not None:
            fit_params = {
                "eval_set": eval_set,
                "verbose": 0,
            }

        init_model = self.get_init_model(dk.pair)

        # Simplify: use plain XGBoost without GridSearchCV for first test
        gs_params = self.freqai_info.get("grid_search_parameters", {})
        use_grid = bool(gs_params) and len(X) > 200

        if use_grid:
            keep_kwargs = {k: v for k, v in self.model_training_parameters.items()
                           if k not in gs_params and k not in ("objective", "eval_metric")}
            base_model = XGBClassifier(
                eval_metric=eval_metric, random_state=42, early_stopping_rounds=50, **keep_kwargs,
            )
            grid = GridSearchCV(base_model, gs_params, cv=min(3, len(X)//50), scoring="roc_auc", n_jobs=1, verbose=0)
            logger.info(f"[FREQAI] Running GridSearchCV with {len(gs_params)} param grids...")
            grid.fit(X=X, y=y, sample_weight=train_weights, xgb_model=init_model, **fit_params)
            logger.info(f"[FREQAI] GS best score: {grid.best_score_:.4f} | best params: {grid.best_params_}")
            result = grid.best_estimator_
        else:
            logger.info(f"[FREQAI] Skipping GridSearchCV (not enough data or no params). Training plain XGBoost...")
            plain_kwargs = {k: v for k, v in self.model_training_parameters.items()
                            if k not in ("objective", "eval_metric")}
            plain_model = XGBClassifier(
                eval_metric=eval_metric, random_state=42, early_stopping_rounds=None,
                **plain_kwargs,
            )
            plain_model.fit(X, y, sample_weight=train_weights, **fit_params)
            logger.info(f"[FREQAI] Plain XGBoost trained successfully")
            result = plain_model

        print(f"[FREQAI MODEL DEBUG] fit() returning model: {type(result).__name__}, is None: {result is None}")
        return result

    def predict(
        self, unfiltered_df: DataFrame, dk: FreqaiDataKitchen, **kwargs
    ) -> tuple[DataFrame, npt.NDArray[np.int_]]:
        dk.find_features(unfiltered_df)
        filtered_df, _ = dk.filter_features(
            unfiltered_df, dk.training_features_list, training_filter=False,
        )

        dk.data_dictionary["prediction_features"] = filtered_df

        dk.data_dictionary["prediction_features"], outliers, _ = dk.feature_pipeline.transform(
            dk.data_dictionary["prediction_features"], outlier_check=True,
        )

        predictions = self.model.predict(dk.data_dictionary["prediction_features"])
        predictions_prob = self.model.predict_proba(dk.data_dictionary["prediction_features"])

        if self.CONV_WIDTH == 1:
            predictions = np.reshape(predictions, (-1, len(dk.label_list)))
            predictions_prob = np.reshape(predictions_prob, (-1, len(self.model.classes_)))

        pred_df = DataFrame(predictions, columns=dk.label_list)
        pred_df_prob = DataFrame(predictions_prob, columns=self.model.classes_)

        pred_df = pd.concat([pred_df, pred_df_prob], axis=1)

        le = LabelEncoder()
        label = dk.label_list[0]
        labels_before = list(dk.data["labels_std"].keys())
        labels_after = le.fit_transform(labels_before).tolist()
        pred_df[label] = le.inverse_transform(pred_df[label])
        pred_df = pred_df.rename(
            columns={labels_after[i]: labels_before[i] for i in range(len(labels_before))}
        )

        if dk.feature_pipeline["di"]:
            dk.DI_values = dk.feature_pipeline["di"].di_values
        else:
            dk.DI_values = np.zeros(outliers.shape[0])
        dk.do_predict = outliers

        return (pred_df, dk.do_predict)
