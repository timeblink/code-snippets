(ns istat.db
  (:require [istat.oracle :refer :all]
            [istat.sqlite :refer [save-into-raw save-into-stat]
                          :rename {
                              save-into-raw raw-save-sqlite
                              save-into-stat stat-save-sqlite}]
            [istat.mongodb  :refer [save-into-raw save-into-stat]
                            :rename {
                              save-into-raw raw-save-mongodb
                              save-into-stat stat-save-mongodb}])
  (:import  [org.apache.commons.lang3.time DateUtils]
            [java.util Calendar]
            [java.util UUID]))

;; Tag: sqlite,insert,update,table raw
(defn raw-save-as [{:keys [dep1 dep2 dep3 code wday wtim1 wtim2]}]
  (let 
    [ uuidx (UUID/nameUUIDFromBytes
        (.getBytes (str dep1 "/" dep2 "/" dep3 "/" code "/" wday)))
      raw-obj { :uuidx (.toString uuidx) :code code
                :dep1 dep1 :dep2 dep2 :dep3 dep3 
                :wday wday :wtim1 wtim1 :wtim2 wtim2}]
    (raw-save-sqlite raw-obj)
    (raw-save-mongodb raw-obj)))

;; Tag: sqlite,sub-fun call
(defn stat-save-as [row-of-stat]
  (doall (map (fn [x]
    (let [
      uuidx (UUID/nameUUIDFromBytes
        (.getBytes (str (x :dep1) "/" (x :dep2) "/" (x :dep3))))
      new-x { :uuidx (.toString uuidx)
              :dep1 (x :dep1) :dep2 (x :dep2) :dep3 (x :dep3) 
              :year (x :year) :week (x :week) :davg (x :davg)}]
      (stat-save-sqlite new-x)
      (stat-save-mongodb new-x)))
    row-of-stat)))

;; Tag: oracle,query,select
(defn timecard-list [{:keys [code date1 date2 depth1 depth2 depth3]}]
  (istat.oracle/get-timecard-list {
    :code code :date1 date1 :date2 date2 
    :depth1 depth1 :depth2 depth2 :depth3 depth3}))

;; Tag: oracle,query,distinct
(defn depth-list [{:keys [depth]}]
  (istat.oracle/get-depth-name {:depth depth}))
