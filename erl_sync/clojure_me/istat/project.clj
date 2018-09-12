(defproject istat "0.1.0"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [
    [org.apache.commons/commons-lang3 "3.4"]
    [org.clojars.gukjoon/ojdbc "1.4"] ;; Oracle jdbc
    [org.xerial/sqlite-jdbc "3.7.2"]  ;; sqlite3
    [mongoika "0.8.7"]                ;; mongodb
    [org.clojure/java.jdbc "0.3.5"]
    [org.clojure/tools.cli "0.2.4"]
    [org.clojure/clojure "1.8.0"]]
  :main istat.core
  :aot [istat.core])
