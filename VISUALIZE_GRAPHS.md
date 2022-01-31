# Neo4j Bloom

The recommended way for **Blue teams and Purple** teams is to **read the analysis performed automatically by PurplePanda with the param `-d` and once some interesting data is found, analyze it in depth with the graphs**.

**Red Teams** should also take a **look to those analysis** and then focus on the **graphs on how to escalate privileges** from the compromised users.

As indicated in the main Readme, it's recommended to download **[Neo4jDesktop](https://neo4j.com/download-center/#desktop)**.

This tool allows you to **run a Neo4j database locally** where you can store all the data gathered by PurplePanda, and it also contains the tool **Neo4jBloom to visualize graphs**.

In this tool you can **save queries, run them and inspect the results** and that is the way in investigate the gathered data in depth.

Each folder inside `/intel` defines one platform that can be enumerated and **contains a `HOW_TO_USE.md` file and a `QUERIES.md` file** with queries to run inside Neo4jBloom to inspect the data. 