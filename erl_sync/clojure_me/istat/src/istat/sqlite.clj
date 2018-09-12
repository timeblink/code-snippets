(ns istat.sqlite
  (:require [clojure.java.jdbc :as sql])
  (:import  [java.util Calendar]
            [java.util UUID]))

(defn- reset-cal [new-time]
  (let
    [cal (Calendar/getInstance)]
    (.setTime cal
      (.parse (java.text.SimpleDateFormat. "yyyy-MM-dd") new-time))
    cal))

(defn raw-schema-init [year]
  (let [
    db {  :classname "org.sqlite.JDBC"
          :subprotocol "sqlite"
          :subname (str "raw" year ".db")}
    schema-str (str "CREATE TABLE IF NOT EXISTS raw("
                    "did TEXT PRIMARY KEY ASC,"
                    "depth1 TEXT,depth2 TEXT,depth3 TEXT,"
                    "code TEXT,wdate TEXT,"
                    "wtim1 TEXT,wtim2 TEXT);")]
    (try (sql/execute! db [schema-str]) (catch Exception e))))

(defn stat-schema-init [year]
  (let [
    db {  :classname "org.sqlite.JDBC"
          :subprotocol "sqlite"
          :subname (str "stat" year ".db")}
    schema-str (str 
      "CREATE TABLE IF NOT EXISTS stat(did TEXT PRIMARY KEY,year TEXT,"
      "depth1 TEXT,depth2 TEXT,depth3 TEXT,"
      (clojure.string/join ", " (map (fn [n] 
          (str "week" n " INTEGER")) 
          (range 1 53))) ");")]
    (try (sql/execute! db [schema-str]) (catch Exception e))))

;; Tag: sqlite,insert,update,table raw
(defn save-into-raw [{:keys [uuidx dep1 dep2 dep3 code wday wtim1 wtim2]}]
  (let [
    cal (reset-cal wday)
    year-str (.get cal Calendar/YEAR)
    dbname (str "raw" year-str ".db")
    db {:classname "org.sqlite.JDBC"
        :subprotocol "sqlite" :subname dbname}
    insert-sql  (str
      "insert into raw (did,depth1,depth2,depth3,code,wdate,wtim1,wtim2"
      ") values('" uuidx "','" dep1 "','" dep2 "','" dep3
      "','" code "','" wday "','" wtim1 "','" wtim2 "')")
    update-sql  (str
      "update raw set wtim1=" wtim1 ",wtim1=" wtim1
      " where did='" uuidx "'")]
    (try (sql/execute! db [insert-sql]) (catch Exception e))
    (try (sql/execute! db [update-sql]) (catch Exception e))))

;; Tag: sqlite,insert,update,table stat
(defn save-into-stat [{:keys [uuidx dep1 dep2 dep3 year week davg]}]
  (let [
    insert-sql  (str
      "insert into stat (did,depth1,depth2,depth3) values('"
      uuidx "','" dep1 "','" dep2 "','" dep3 "')")
    update-sql  (str
      "update stat set week" week "=" davg
      " where did='" uuidx "'")
    db {  :classname "org.sqlite.JDBC"
          :subprotocol "sqlite"
          :subname (str "stat" year ".db")}]
    (try (sql/execute! db [insert-sql]) (catch Exception e))
    (try (sql/execute! db [update-sql]) (catch Exception e))))