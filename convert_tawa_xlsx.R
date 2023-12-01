library(TAWApost)

input_path <- "input/TAR295_postCPI_rep100_2021-09-29-114831.xlsx"

people <- combine_stats_output(input_path)

# save to csv
write.csv(people, "input/tawa.csv", row.names = FALSE)

