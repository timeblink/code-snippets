(ns istat.core
  (:import  [org.apache.commons.lang3.time DateUtils]
            [java.util Calendar])
  (:require [istat.db :refer :all]
            [istat.stat :refer :all]
            [mongoika :refer :all])
  (:use [clojure.tools.cli :only [cli]])
  (:gen-class))

(defn- base-depth-stat [time1,time2]
  ;;设定查询条件，限定部门
  (let 
    [condition {:depth1 (istat.db/depth-list {:depth "L1"})
                :depth2 (istat.db/depth-list {:depth "L2"})
                :depth3 (istat.db/depth-list {:depth "LAST"})
                :date1 time1 :date2 time2}]
    (istat.db/stat-save-as
      (istat.stat/stat-workday 
        (istat.db/timecard-list condition)))))

(defn- add-depth-stat [time1,time2]
  ;;设定查询条件，限定部门，为了适应NC的部门设置，需要再查一次，将数据补全
  (let
    [condition {:depth2 (istat.db/depth-list {:depth "L2"})
                :depth3 (istat.db/depth-list {:depth "LAST"})
                :date1 time1 :date2 time2}]
    (istat.db/stat-save-as 
      (istat.stat/stat-workday 
        (istat.db/timecard-list condition)))))

(defn- week-stat [week]
  (let 
    [ time2 (Calendar/getInstance)
      x (.set time2 Calendar/YEAR (week :year))
      x (.set time2 Calendar/MONTH Calendar/JANUARY)
      x (.set time2 Calendar/DATE 1)
      x (.set time2 Calendar/DATE (* (week :week) 7))
      time1 (DateUtils/addDays (.getTime time2) -7)
      ti1 (.format (java.text.SimpleDateFormat. "yyyy-MM-dd") time1)
      ti2 (.format 
        (java.text.SimpleDateFormat. "yyyy-MM-dd") (.getTime time2))]
    (istat.sqlite/stat-schema-init (week :year))
    (istat.sqlite/raw-schema-init (week :year))
    (base-depth-stat ti1 ti2)
    (add-depth-stat ti1 ti2)))

(defn application [opts]
  (let 
    [ cal (Calendar/getInstance)
      time-s (.parse (java.text.SimpleDateFormat. "yyyy-MM-dd") (opts :start))
      time-e (.parse (java.text.SimpleDateFormat. "yyyy-MM-dd") (opts :end))
      time-gap (/ (- (.getTime time-e) (.getTime time-s)) (* 24 60 60 1000))
      week-of-year-list (map 
        (fn [x] (let [
          tim1 (DateUtils/addDays time-s x)
          cal1 (Calendar/getInstance)
          tmp1 (.setTime cal1 tim1)]
          { :week (.get cal1 Calendar/WEEK_OF_YEAR)
            :year (.get cal1 Calendar/YEAR)}))
        (range 0 time-gap))]
    (doall (map (fn [y] (week-stat y)) (distinct week-of-year-list)))))

(defn debugme [opts]
  (let 
    [ host "192.168.15.33" 
      port 27019
      dbname "ibusy"
      cname "RawOfTimecard"]
    (with-mongo [connection {:host "192.168.15.33" :port 27019}]
      (with-db-binding (database connection "ibusy")
        (println 
          (count 
            (restrict 
              :uuidx "99acb6c2-90b3-3380-96f2-5bb944b970bf" cname)
          ))))))

(defn -main [& args]
  (let [
    cal (Calendar/getInstance)
    time-e (.getTime cal)
    time-s (DateUtils/addDays time-e (* 7 -5))
    time-s-str (.format (java.text.SimpleDateFormat. "yyyy-MM-dd") time-s)
    time-e-str (.format (java.text.SimpleDateFormat. "yyyy-MM-dd") time-e)
    [options args banner] (cli args
      ["--help" "show help" :default false :flag true]
      ["--[no-]debug" "debug mode" :default false]
      ["--[no-]verbose" "verbose mode" :default false]
      ["--start" "set update last week" :default time-s-str]
      ["--end" "set update last week" :default time-e-str])]
    (when (:help options) (println banner) (System/exit 0))
    (if (options :debug) (debugme options) (application options))))