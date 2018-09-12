(defproject cherrypick "0.1.0"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [
    [clj-http "2.3.0"]
    [org.clojure/tools.cli "0.2.4"]
    [org.clojure/clojure "1.8.0"]]
  :main cherrypick.core
  :aot [cherrypick.core])
