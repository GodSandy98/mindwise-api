WITH raw_all AS (
  SELECT
    a.student_id AS student_id,
    qi.indicator_id AS indicator_id,
    AVG(
      CASE
        WHEN q.is_negative = 1 THEN (q.num_choices + 1 - a.answer)
        ELSE a.answer
      END
    ) AS score_raw
  FROM answers a
  JOIN questions q
    ON q.id = a.question_id
  JOIN indicator_question qi
    ON qi.question_id = q.id
  WHERE a.release = :release
  GROUP BY a.student_id, qi.indicator_id
)
SELECT
  indicator_id AS indicator_id,
  AVG(score_raw) AS mean,
  (AVG(score_raw * score_raw) - AVG(score_raw) * AVG(score_raw)) AS variance
FROM raw_all
GROUP BY indicator_id;
