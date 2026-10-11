# OULAD Sample Dataset

This directory contains representative sample slices from the Open University Learning Analytics Dataset (OULAD) to enable rapid local evaluation, testing, and exploration without downloading the multi-gigabyte raw archive.

## Included Sample Files

1. `courses.csv`: Full course catalog detailing course modules (`AAA`, `BBB`, etc.) and presentations (`2013J`, `2014J`, etc.) along with presentation duration in days.
2. `assessments.csv`: Assessment structure across modules with assessment types (TMA, CMA, Exam), deadlines, and percentage weights.
3. `studentInfo.csv`: Sample demographic and registration records for 150 students including `id_student`, `code_module`, `code_presentation`, `gender`, `region`, `highest_education`, `imd_band`, `age_band`, `num_of_prev_attempts`, `studied_credits`, `disability`, and `final_result`.
4. `studentRegistration.csv`: Enrolment dates and unregistration dates for the sample students.
5. `studentAssessment.csv`: Submission dates and scored assessments for the sampled students.
6. `vle.csv`: VLE resource catalog describing learning activities (oucontent, forumng, quiz, resource, url, subpage, glossary).
7. `studentVle.csv`: Detailed clickstream interaction logs (student ID, site ID, date relative to course start, sum of clicks).

All foreign keys and student identifiers (`id_student`) are referentially consistent across all 7 CSV tables.
