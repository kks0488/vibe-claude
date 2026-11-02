# Keeping a Founder's Words From Vanishing Across 33 Registered AI Sessions, and Recovering After a System Stop

In a small company running on AI sessions, operational risk shifts to message routing. Our company has one founder who does not write code. If you operate a one-to-five person company using Claude Code or Codex for paid work, you face a similar challenge: making sure the founder's instructions do not disappear.

In our setup, work runs through one command session and multiple team sessions using Claude Code, while hands-on tasks are handled by other engines such as Codex. Our task board has 33 assignee sessions registered in the tool. That figure is the registered count rather than the number of sessions alive at once, and it requires a reliable way to track who owns what.

We built a tracking pipeline using plain files and the open-source task tool Vikunja. Below is how the mechanism works, what nine days of read-only numbers show, what still fails, and how we recovered when our scheduler stopped.

## The Seven-Step Directive Pipeline

We capture the founder's words and turn them into tracked cards in Vikunja through seven steps.

1. An input logger in the command session filters incoming text and records only what the founder types directly, excluding forwarded messages from other sessions and scheduled alerts.
2. The logger writes each recorded input line by line into a file first.
3. An import command creates cards in the Directives column in Vikunja, using a short identifier made from the recorded timestamp and content to avoid creating duplicate cards from the same line.
4. The system attaches a single assignee session to the card and removes any other assignee labels.
5. Large tasks are split into separate task cards that carry the original directive identifier and an item number so the same task is not created twice.
6. The assigned session leaves evidence of the result and closes the card.
7. An audit command repeatedly surfaces unassigned directives, directives unprocessed for over 3 hours, overdue task cards, and task cards stalled for 3 days.

## Nine Days of Read-Only Numbers

In the early morning of 2026-11-03, we ran a read-only check covering the nine-day period from 2026-10-25 to 2026-11-03.

| Metric | Count or Value (2026-10-25 to 2026-11-03) | Context |
| :--- | :--- | :--- |
| Directive cards | 3,121 | Directive cards visible at check time, created 2026-10-25 to 2026-11-03 |
| Closed directive cards | 3,120 | Closed during the nine-day window |
| Open directive cards | 1 | Remaining open at check time |
| Unassigned open directives | 0 | Open directives without an owner |
| Median time from card creation to closure | 13 minutes 45 seconds | Card creation to card closure only |
| General task cards | 2,447 | Separate task cards outside Directives |
| Open general task cards | 287 | Remaining open at check time |
| Overdue task cards | 46 | Can overlap with 3-day stalled cards |
| Task cards stalled for 3 days | 60 | Can overlap with overdue cards |

The median time of 13 minutes 45 seconds measures only the duration from when a directive card was created to when that card was closed. It does not measure the time from the moment the founder typed the input, nor does it represent the time when the underlying work was completely finished.

## What Still Does Not Work

Our read-only audit on 2026-11-03 also showed several parts of the pipeline that do not work as intended yet.

First, short identifiers did not prevent all duplicates. We found 2 groups where the same short identifier remained on multiple cards, accounting for 5 cards in total and 3 excess cards. The cause is still unconfirmed.

Second, 3,120 closed directive cards do not mean 3,120 completed jobs. Closed cards may include simple acknowledgments or handoffs to other cards; this audit did not verify individual closure reasons. Our own card command also does not block a session from closing a card without result evidence. It only flags it.

Third, the built-in link between a directive and its task cards is not being used yet. The number of task cards that carried the standard linking line was 0. The links we could confirm were written by hand as card numbers, covering at least 11 directives and 4 task cards.

Fourth, we have not measured the input omission rate. We do not yet know whether every direct input typed by the founder was recorded in the file without any drops.

## The October 26 Failure and Recovery

On 2026-10-26, the server ran out of memory, which killed the task scheduler, cron. As a result, our scheduled jobs stopped.

On that same day, a session watchdog script restarted one secretary session and one production session. In our operational logs, the gap between the stop timestamp and the restart record was about 44 minutes. Because our operational logs record time in minute units, 44 minutes is not an exact recovery duration. Also, we cannot confirm from the logs who noticed the issue first.

This outage exposed a clear limitation in our watchdog script. The watchdog only checks whether a session name exists and opens a new session if it is missing. It does not check whether that session actually resumed doing its work.

After the incident, we made three changes to our setup. First, we protected the cron scheduler so it does not die easily and configured it to restart automatically if it stops. Second, we separated the tmux server, which is the underlying program that hosts our sessions, into a separate service so it does not die along with the scheduler. Third, we limited browser memory usage.

## Lessons From Running the System

We learned five practical lessons from operating this setup.

First, words must be written to a file first so they survive even if a session dies. Second, every card must have only one assignee session. Third, closing a card requires leaving evidence of the result. Fourth, system checks must be done with numbers every time, tracking unassigned items, 3-hour delays, overdue tasks, and 3-day stalls. Fifth, restarting a session is different from recovering the work: opening a missing session name does not prove the work is moving again.

## Copy-Paste Card Template

You can copy the Markdown block below to structure directive and task cards in your own tracker.

```markdown
Card Type: [Directive | Task]
Short Identifier (Timestamp + Content): 
Assigned Session (Single Assignee Only): 
Original Directive ID (If Split Task): 
Original Directive Item Number (If Split Task): 

Instruction or Task Summary:
[Record direct founder input or split task scope]

Closure Record:
Closure Type: [Work Completed | Acknowledged | Handed Off to Task Card]
Result Evidence:
[Record concrete result evidence before closing]
```
