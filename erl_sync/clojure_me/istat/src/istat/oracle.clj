(ns istat.oracle
  (:require [clojure.java.jdbc :as sql])
  (:import  [org.apache.commons.lang3.time DateUtils]
            [java.util Calendar]))

;; Tag: oracle,sql
(defn create-query-sql [{:keys [code date1 date2 depth1 depth2 depth3]}]
  (str  "SELECT " ;;生成sql语句
        "CODE,CALENDARDATE,CALENDARTIME,L1,L2,LAST "
        "FROM nc63.ThunderSoftWorktimeView "
        "WHERE TO_TIMESTAMP(CALENDARDATE,'YYYY-MM-DD') >= TO_TIMESTAMP('"
        (if date1 date1 ;;如果参数中不设定时间，默认取当前日期所在周的第一天
          (.format
            (java.text.SimpleDateFormat. "yyyy-MM-dd")
            (DateUtils/addDays  (.getTime (Calendar/getInstance))
                                (- 2 (.get (Calendar/getInstance)
                                        Calendar/DAY_OF_WEEK)))))
        "','YYYY-MM-DD')"
        " AND TO_TIMESTAMP(CALENDARDATE,'YYYY-MM-DD') <= TO_TIMESTAMP('"
        (if date2 date2 ;;如果参数中不设定时间，默认取当前日期
          (.format
            (java.text.SimpleDateFormat. "yyyy-MM-dd")
            (.getTime (Calendar/getInstance))))
        "','YYYY-MM-DD')"
        " AND LAST != '离职人员管理中心'" ;;忽略这个组织结构的数据
        (if code ;;如果参数设定则生效，调试接口
          (str " AND CODE = '" code "'") "")
        (if depth1 ;;一级部门查询条件
          (str " AND L1 in ('"
            (reduce (fn [m v] (str m "','" v )) depth1) "')") "")
        (if depth2 ;;二级部门查询条件
          (str " AND L2 in ('"
            (reduce (fn [m v] (str m "','" v )) depth2) "')") "")
        (if depth3 ;;三级部门查询条件，nc系统最大深度就是三级
          (str " AND LAST in ('"
            (reduce (fn [m v] (str m "','" v )) depth3) "')") "")
        " order by L1,L2,LAST,CODE,CALENDARDATE,CALENDARTIME"))

;; Tag: oracle,query,select
(defn get-timecard-list [{:keys [code date1 date2 depth1 depth2 depth3]}]
  (let [
    sql-str (create-query-sql {
              :code code :date1 date1 :date2 date2
              :depth1 depth1 :depth2 depth2 :depth3 depth3})]
    (sql/query ;;jdbc查询方法
      { :classname "oracle.jdbc.OracleDriver" ;;定义oracle的jdbc driver
        :subprotocol "oracle"
        :subname "thin:@192.168.8.103:1521:ncdb"
        :user "tswk" :password "tsinner15943"}
      [sql-str]
      :row-fn (fn [row] ;;返回结果的数据格式
        (sorted-map :code (row :code),
                    :dep1 (if (row :l1) (row :l1) (row :l2)),
                    :dep2 (if (row :l1) (row :l2) (row :last)),
                    :dep3 (if (row :l1) (row :last) "直属"),
                    :wday (row :calendardate),
                    :wtim (row :calendartime))))))

;; Tag: oracle,query,distinct
(defn get-depth-name [{:keys [depth]}]
  (let [
    sql-str (str "SELECT DISTINCT " depth " as DEP "
      "FROM nc63.ThunderSoftWorktimeView "
      "WHERE LAST != '离职人员管理中心'")]
    (sql/query ;;jdbc查询方法
      { :classname "oracle.jdbc.OracleDriver" ;;定义oracle的jdbc driver
        :subprotocol "oracle"
        :subname "thin:@192.168.8.103:1521:ncdb"
        :user "tswk" :password "tsinner15943"}
      [sql-str]
      :row-fn (fn [row] (row :dep)))))
