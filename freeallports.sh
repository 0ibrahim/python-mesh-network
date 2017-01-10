
#!/bin/bash
# Listing the planets.

for port in 2000 3000
do
  freeport -h $port  # Each planet on a separate line.
done