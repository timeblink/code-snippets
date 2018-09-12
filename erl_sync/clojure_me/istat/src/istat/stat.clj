(ns istat.stat
  ;;----------------------------------------------------------------------------
  (:import  [org.apache.commons.lang3.time DateUtils]
            [java.util Calendar])
  (:require [istat.sqlite :refer :all]))

(defn- reset-time [new-time]
  (let 
    [cal (Calendar/getInstance)]
    (.setTime cal
      (.parse
        (java.text.SimpleDateFormat. "yyyy-MM-dd HH:mm:ss")
          new-time))
    cal))

(defn sum-of-work-fun [rtime1,rtime2]
  ;;----------------------------------------------------------------------------
  (let  [ cal1 (reset-time rtime1)
          cal2 (reset-time rtime2)
          sum-day (- (.getTimeInMillis cal2) (.getTimeInMillis cal1))]
        (- (/ sum-day (* 3600.0 1000.0)) 1)))

(defn workx [x,type,res]
  ;;----------------------------------------------------------------------------
  ;;实现一个功能，就算一个人在给定范围内的有效打卡工时
  ;;这个功能函数，根据参数返回不同的统计结果
  ;;通用规则，同一日至少打卡两次，且两次打卡间隔超过6小时
  ;;type = s 返回一个列表，其中也包括周末的打卡工时
  ;;type = w 返回一个列表，有效的工作日计数
  ;;type = e 返回一个列表，有效的周末加班计数
  (reduce + (doall  (map
    (fn [w] ;;实现一个功能，计算某个人当天的有效打卡工时
      (let 
        [ times (filter (fn [u] (= true ;; 拿到某个人在某一天的刷卡记录
                              (= (u :dep1) (x :dep1))
                              (= (u :dep2) (x :dep2))
                              (= (u :dep3) (x :dep3))
                              (= (u :code) (x :code))
                              (= (u :wday) (w :wday)))) res)
          tim1 (first times)
          tim2 (last times)
          sum-work (sum-of-work-fun (tim1 :wtim) (tim2 :wtim))
          cal3 (Calendar/getInstance)
          tmp (.setTime cal3 (.parse  
                (java.text.SimpleDateFormat. "yyyy-MM-dd")
                (w :wday)))
          week-num (.get cal3 Calendar/DAY_OF_WEEK)]
        (istat.db/raw-save-as {
          :dep1 (x :dep1) :dep2 (x :dep2) :dep3 (x :dep3)
          :code (x :code) :wday (w :wday)
          :wtim1 (tim1 :wtim) :wtim2 (tim2 :wtim)})
        (case type
          "s" (if (>= (count times) 2)
                (if (> sum-work 6) sum-work 0) 0)
          "w" (if (= (mod week-num 7) 0)
                0 (if (>= (count times) 2) (if (> sum-work 6) 1 0) 0))
          "e" (if (= (mod week-num 7) 0)
                (if (>= (count times) 2) (if (> sum-work 6) 1 0) 0) 0)
          0)))
    (distinct ;; 获得某个人所有打卡的日期
      (doall (map
        (fn [z] {:wday (z :wday)})
        (filter (fn [y] (= true
                        (= (y :dep1) (x :dep1))
                        (= (y :dep2) (x :dep2))
                        (= (y :dep3) (x :dep3))
                        (= (y :code) (x :code)))) res))))))))

(defn cal-result-depth [dep-work-list,res]
  ;;----------------------------------------------------------------------------
  ;;(println (count dep-work-list))
  ;;实现一个功能，计算这个部门的平均指数
  (let 
    [ sum-of-work ( ;;拿到每个人有效的工时合计
        reduce + (doall (map (fn [x] (workx x "s" res)) dep-work-list)))
      count-of-workday ( ;;拿到每个人有效的工作日
        reduce + (doall (map (fn [x] (workx x "w" res)) dep-work-list)))]
    (+ (/ (/ (- sum-of-work (* 
      count-of-workday 8.00)) count-of-workday) 10.00) 1.00)))

(defn count-man-of-dep [work,res]
  ;;----------------------------------------------------------------------------
  ;; 定义一个方法，获取一个部门中，参与指数计算的有效员工数
  ;; 这个是测试，用来按照部门筛选记录
  ;; 没解决的问题，如果员工打卡记录不符合计算规则，这个列表中是没有过滤掉的
  (let 
    [ x work
      man-of-dep (distinct (doall (map 
        (fn [x] { :dep1 (x :dep1) :dep2 (x :dep2) 
                  :dep3 (x :dep3) :code (x :code)})
        (filter (fn [u] (= true
                        (= (u :dep1) (x :dep1))
                        (= (u :dep2) (x :dep2))
                        (= (u :dep3) (x :dep3)))) res))))]
    (count man-of-dep)))

(defn stat-workday [row-of-cards]
  ;;----------------------------------------------------------------------------
  (def res row-of-cards)
  (doall
   (map ;;根据排重后部门清单进行遍历
    (fn [x] ;;提取到某个部门下面所有人的记录
      (let [
        row-of-depth (filter  (fn [y] 
          (= true (= (y :dep1) (x :dep1))
                  (= (y :dep2) (x :dep2))
                  (= (y :dep3) (x :dep3)))) res)
        dep-work-list (distinct (doall (map (fn [z] 
                        { :dep1 (z :dep1) :dep2 (z :dep2)
                          :dep3 (z :dep3) :code (z :code)}) 
                        row-of-depth)))
        year-num  (first (distinct (doall (map (fn [z]
          (let [cal3 (Calendar/getInstance)]
            (.setTime cal3 
              (.parse (java.text.SimpleDateFormat. "yyyy-MM-dd") (z :wday)))
            {:ynum (.get cal3 Calendar/YEAR)}))
          res))))
        week-num  (first (distinct (doall (map (fn [z]
          (let [cal3 (Calendar/getInstance)]
            (.setTime cal3 
              (.parse (java.text.SimpleDateFormat. "yyyy-MM-dd") (z :wday)))
            {:wnum (.get cal3 Calendar/WEEK_OF_YEAR)}))
          res))))]
        { :dep1 (x :dep1) :dep2 (x :dep2) :dep3 (x :dep3)
          :week (week-num :wnum) :year (year-num :ynum)
          :davg (cal-result-depth dep-work-list res)}))
    (distinct ;;获得去重后的部门清单
     (doall
      (map (fn [x] {:dep1 (x :dep1) :dep2 (x :dep2) :dep3 (x :dep3)}) res))))))
