from locust import HttpUser, between, task

good_payload_row = {
  "gender": "Female",
  "age": 44,
  "hypertension": 0,
  "heart_disease": 0,
  "smoking_history": "never",
  "bmi": 19.31,
  "HbA1c_level": 6.5,
  "blood_glucose_level": 200
}

class DiabetesPredictionServiceUser(HttpUser):

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
            