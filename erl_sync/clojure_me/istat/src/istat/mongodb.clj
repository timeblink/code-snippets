(ns istat.mongodb
  (:require [mongoika :refer :all])
  (:import  [org.apache.commons.lang3.time DateUtils]
            [java.util Calendar]))

(defn save-into-stat [{:keys [uuidx dep1 dep2 dep3 year week davg]}]
  (let 
    [ host "192.168.15.33" 
      port 27019
      dbname "ibusy"
      cname "StatOfTimecard"
      insert-obj {:uuidx uuidx  
                  :dep1 dep1 :dep2 dep2 :dep3 dep3 
                  :year year :week week :davg davg}]
    (with-mongo [connection {:host host :port port}]
      (with-db-binding (database connection dbname)
        (if (== 0 (count (restrict :uuidx uuidx cname)))
          (insert! cname insert-obj))))))

(defn save-into-raw [{:keys [uuidx dep1 dep2 dep3 code wday wtim1 wtim2]}]
  (let 
    [ host "192.168.15.33" 
      port 27019
      dbname "ibusy"
      cname "RawOfTimecard"
      insert-obj {:uuidx uuidx :dep1 dep1 :dep2 dep2 :dep3 dep3
                  :code code :wday wday :wtim1 wtim1 :wtim2 wtim2}]
    (with-mongo [connection {:host "192.168.15.33" :port 27019}]
      (with-db-binding (database connection "ibusy")
        (if (== 0 (count (restrict :uuidx uuidx cname)))
          (insert! cname insert-obj))))))