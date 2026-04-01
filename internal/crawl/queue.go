package crawl

import "fmt"

type Queue interface {
	Enqueue(Job) error
	Dequeue() (Job, bool)
	Len() int
}

type MemoryQueue struct {
	jobs      []Job
	scheduled map[string]struct{}
}

func NewMemoryQueue() *MemoryQueue {
	return &MemoryQueue{
		scheduled: make(map[string]struct{}),
	}
}

func (q *MemoryQueue) Enqueue(job Job) error {
	normalized, err := NormalizeURL(job.URL)
	if err != nil {
		return err
	}
	key := fmt.Sprintf("%s|%s", job.AuditID, normalized)
	if _, exists := q.scheduled[key]; exists {
		return nil
	}

	job.URL = normalized
	q.jobs = append(q.jobs, job)
	q.scheduled[key] = struct{}{}
	return nil
}

func (q *MemoryQueue) Dequeue() (Job, bool) {
	if len(q.jobs) == 0 {
		return Job{}, false
	}
	job := q.jobs[0]
	q.jobs = q.jobs[1:]
	return job, true
}

func (q *MemoryQueue) Len() int {
	return len(q.jobs)
}
