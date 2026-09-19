from locust import HttpUser, task, between


good_payload_row = {
  "gender": "Female",
  "SeniorCitizen": 0,
  "Partner": "Yes",
  "Dependents": "No",
  "tenure": 5,
  "PhoneService": "Yes",
  "MultipleLines": "No",
  "InternetService": "Fiber optic",
  "OnlineSecurity": "No",
  "OnlineBackup": "No",
  "DeviceProtection": "No",
  "TechSupport": "No",
  "StreamingTV": "Yes",
  "StreamingMovies": "Yes",
  "Contract": "Month-to-month",
  "PaperlessBilling": "Yes",
  "PaymentMethod": "Electronic check",
  "MonthlyCharges": 89.5,
  "TotalCharges": 445.2
}

class ChurnPredictionServiceUser(HttpUser):

    wait_time = between(0.3, 1.2)

    @task(1)
    def predict(self):
        with self.client.post(
            "/v1/predict",
            json=good_payload_row,
            catch_response=True
        ) as post_response:
            if post_response.status_code != 200:
                post_response.failure("Ошибка! Код ответа {post_response.status_code}")
                return
            