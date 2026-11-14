# Work clock: $slug

One row per sitting. Start is the session's first message; End is its wrap-up. Minutes is what the sitting took; Active, when set, is the time actually worked (the session sat idle). Totals count Active when set, else Minutes. Times carry their UTC offset. `projects.py clock add` appends a row at wrap-up; `projects.py clock` shows the totals.

| Start | End | Minutes | Active | Changelog | Note |
|-------|-----|---------|--------|-----------|------|
