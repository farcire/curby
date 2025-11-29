# 📊 AI Restriction Interpretation Report

> **Evaluation Summary**
> - **Model:** `gemini-2.0-flash`
> - **Date:** 2025-11-29 00:02:04
> - **Pass Rate:** 33.3% (4/12)
> - **Avg Score:** 0.42

## 🧪 Test Case Results

| ID | Object ID | Score | Status | Original Text |
|:---|:---:|:---:|:---:|:---|
| test_case_1 | 4134 | 0.0 | ❌ FAIL | Limited No Parking Regulation is due to the DPW Pit Stop pro... |
| test_case_2 | 2809 | 0.0 | ❌ FAIL | No oversized vehicles Oversized vehicles and trailers are th... |
| test_case_3 | 4341 | 1.0 | ✅ PASS | Time limited MM. ESTABLISH – 4-HOUR TIME LIMIT, 8 AM TO 6 PM... |
| test_case_4 | 2112 | 1.0 | ✅ PASS | No overnight parking |
| test_case_5 | 4048 | 1.0 | ✅ PASS | No parking any time |
| test_case_6 | 1401 | 1.0 | ✅ PASS | Government permit |
| test_case_7 | 1113 | 0.5 | ⚠️ WARN | Time limited |
| test_case_8 | 3950 | 0.0 | ❌ FAIL | Time Limited |
| test_case_9 | 3376 | 0.0 | ❌ FAIL | Limited No Parking |
| test_case_10 | 1032 | 0.0 | ❌ FAIL | Time limited 11-117 |
| test_case_11 | 682 | 0.5 | ⚠️ WARN | Time limited 12-119 |
| test_case_12 | 1669 | 0.0 | ❌ FAIL | Time limited 08-183, 230718-060 |

## 🔍 Failed Cases Analysis

### test_case_1 (ObjID: 4134) `Score: 0.0`
**📝 Original Text:**
> Limited No Parking Regulation is due to the DPW Pit Stop program (https://sfpublicworks.wixsite.com/pitstop)

**🤔 Reasoning:**
The interpretation hallucinates both the days and time ranges. The original text only mentions the 'DPW Pit Stop program', implying a No Parking regulation is in effect but does not provide any specific days or times. The interpretation provides "Monday-Friday, 10:00 AM to 7:00 PM" without evidence, which is a critical safety error, as a user may rely on this hallucinated information, leading to a tow.

---

### test_case_2 (ObjID: 2809) `Score: 0.0`
**📝 Original Text:**
> No oversized vehicles Oversized vehicles and trailers are those longer than 22 feet or taller than 7 feet

**🤔 Reasoning:**
The original text states "No oversized vehicles Oversized vehicles and trailers are those longer than 22 feet or taller than 7 feet". The interpretation includes a time range where this restriction applies (00:00-06:00 daily). This is a hallucination. There's no temporal information within the raw text. By adding a time constraint that does not exist, it creates a false sense of security for the remaining time in the day. If someone were to park their oversized vehicle during the time not in the rule, they would be at risk of getting ticketed or towed.

---

### test_case_7 (ObjID: 1113) `Score: 0.5`
**📝 Original Text:**
> Time limited

**🤔 Reasoning:**
The interpretation assumes 'Time limited' implies a Monday-Friday restriction from 8 AM to 6 PM, and a 2-hour limit, which are not explicitly stated in the original text. It also hallucinates the U permit exception. The original text is too vague to determine accuracy, and the interpretation fills in too many unstated details.

---

### test_case_8 (ObjID: 3950) `Score: 0.0`
**📝 Original Text:**
> Time Limited

**🤔 Reasoning:**
Evaluation error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-2.0-flash
Please retry in 59.276499688s. [links {
  description: "Learn more about Gemini API quotas"
  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
}
, violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.0-flash"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
  quota_value: 15
}
, retry_delay {
  seconds: 59
}
]

---

### test_case_9 (ObjID: 3376) `Score: 0.0`
**📝 Original Text:**
> Limited No Parking

**🤔 Reasoning:**
Evaluation error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-2.0-flash
Please retry in 58.975838133s. [links {
  description: "Learn more about Gemini API quotas"
  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
}
, violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.0-flash"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
  quota_value: 15
}
, retry_delay {
  seconds: 58
}
]

---

### test_case_10 (ObjID: 1032) `Score: 0.0`
**📝 Original Text:**
> Time limited 11-117

**🤔 Reasoning:**
Evaluation error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-2.0-flash
Please retry in 57.132899231s. [links {
  description: "Learn more about Gemini API quotas"
  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
}
, violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.0-flash"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
  quota_value: 15
}
, retry_delay {
  seconds: 57
}
]

---

### test_case_11 (ObjID: 682) `Score: 0.5`
**📝 Original Text:**
> Time limited 12-119

**🤔 Reasoning:**
The interpretation correctly identifies that it cannot fully understand the parking restriction. However, it doesn't provide any structured data, which is not ideal. It also classifies the severity as 'medium,' which is appropriate given the uncertainty. Flagging this because the lack of structured data limits usability.

---

### test_case_12 (ObjID: 1669) `Score: 0.0`
**📝 Original Text:**
> Time limited 08-183, 230718-060

**🤔 Reasoning:**
Evaluation error: 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. To monitor your current usage, head to: https://ai.dev/usage?tab=rate-limit. 
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 15, model: gemini-2.0-flash
Please retry in 55.309475692s. [links {
  description: "Learn more about Gemini API quotas"
  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
}
, violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.0-flash"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
  quota_value: 15
}
, retry_delay {
  seconds: 55
}
]

---
